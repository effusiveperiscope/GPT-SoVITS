# 0. Config
# %%
ANNOTATION_FILELIST_DIR = "" # /{exp name}.list
WAVDIR = "" # Root for wav file paths
EXPS = [
    {
        "name": "Twilight-32",
        "filelist_name": "Twilight",
        "sovits_lora_rank": 32,
        "sovits_epochs": 2,
        "gpt_epochs": 24
    }
]
BERT_PRETRAINED_DIR = "GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large"
CNHUBERT_BASE_DIR = "GPT_SoVITS/pretrained_models/chinese-hubert-base"
# Note that there are two new pretrained models for v3
S2G_MODEL_DIR = "GPT_SoVITS/pretrained_models/s2Gv3.pth"
GPT_PRETRAINED_DIR = "GPT_SoVITS/pretrained_models/s1v3.ckpt"
SOVITS_BATCH_SIZE = 16
SOVITS_SAVE_FREQUENCY = 1
SOVITS_LOW_LR_RATE = 0.4 # default value, hasn't caused issues
GPT_BATCH_SIZE = 8
GPT_SAVE_FREQUENCY = 8

# Check for pretrained models
assert os.path.exists(BERT_PRETRAINED_DIR)
assert os.path.exists(CNHUBERT_BASE_DIR)
assert os.path.exists(S2G_MODEL_DIR)
assert os.path.exists(GPT_PRETRAINED_DIR)

# 1. dataset formatting
from tools import my_utils
from tools.my_utils import load_audio
from config import python_exec,infer_device,is_half,exp_root,webui_port_main,webui_port_infer_tts,webui_port_uvr5,webui_port_subfix,is_share
from subprocess import run
from shutil import copy2, move
import pandas as pd

now_dir = os.getcwd()
tmp_dir = os.path.join(now_dir, "TEMP")
os.makedirs(tmp_dir, exist_ok=True)
os.environ["TEMP"] = tmp_dir

# vocal_path|speaker_name|language|text

def dataset_formatting(exp):
    annotation_filelist = os.path.join(ANNOTATION_FILELIST_DIR, f"{exp['filelist_name']}.list")

    annotation_filelist = my_utils.clean_path(annotation_filelist)
    wavdir = my_utils.clean_path(WAVDIR)

    opt_dir = f'{exp_root}/{exp["name"]}'

    # Perform some checks
    assert os.path.exists(annotation_filelist)
    if (len(wavdir)):
        assert os.path.exists(wavdir)
        assert os.path.isdir(wavdir)

    with open(annotation_filelist,"r",encoding="utf8") as f:
        line=f.readline().strip("\n")
        wav_path, _, __, ___ = line.split("|")
        wav_path=my_utils.clean_path(wav_path)
        wav_path = os.path.join(wavdir, wav_path)
        if not os.path.exists(wav_path):
            raise FileNotFoundError(wav_path)

    config = {
        "inp_text": annotation_filelist,
        "inp_wav_dir": wavdir,
        "exp_name": exp['name'],
        "opt_dir": f"{exp_root}/{exp['name']}",
        "bert_pretrained_dir": BERT_PRETRAINED_DIR,

        # We assume a single GPU for this setup
        "i_part": "0",
        "all_parts": "1",
        "_CUDA_VISIBLE_DEVICES": "0",
        "is_half": str(is_half)
    }

    os.environ.update(config) # Really? It passes variables by OS environment? seems brittle
    
    # 1. Tokenization (phonemization?) & BERT Feature Extraction
    print("1. Tokenization & BERT Feature Extraction")
    path_text = f"{opt_dir}/2-name2text.txt"
    
    if not os.path.exists(path_text):
        cmd = f"{python_exec} GPT_SoVITS/prepare_datasets/1-get-text.py"
        p = run(cmd, shell=True, stdout=open(f'{opt_dir}/1-stdout.log', 'w'))

        # -0.txt is generated for GPU 0; there would be more if we used multiple GPUs
        assert os.path.exists(f"{opt_dir}/2-name2text-0.txt")
        move(f"{opt_dir}/2-name2text-0.txt", f"{opt_dir}/2-name2text.txt")

    # 2. Speech SSL Feature Extration
    print("2. Speech SSL Feature Extraction")
    config.update({
        "cnhubert_base_dir": CNHUBERT_BASE_DIR
    })
    os.environ.update(config)

    cmd = f"{python_exec} GPT_SoVITS/prepare_datasets/2-get-hubert-wav32k.py"
    p = run(cmd, shell=True, stdout=open(f'{opt_dir}/2-stdout.log', 'w'))

    # 3. Semantic token extraction
    print("3. Semantic token extraction")
    path_semantic = f"{opt_dir}/6-name2semantic.tsv"
    config.update({
        "pretrained_s2G": S2G_MODEL_DIR,
        "s2config_path": "GPT_SoVITS/configs/s2.json"
    })

    if not os.path.exists(path_semantic):
        cmd = f"{python_exec} GPT_SoVITS/prepare_datasets/3-get-semantic.py"
        p = run(cmd, shell=True, stdout=open(f'{opt_dir}/3-stdout.log', 'w'))

        # (why did they switch to .tsv?)
        assert os.path.exists(f"{opt_dir}/6-name2semantic-0.tsv")
        opt = ["item_name\tsemantic_audio"] # header

        with open(f"{opt_dir}/6-name2semantic-0.tsv","r",encoding="utf8") as f:
            opt += f.readlines()
        with open(f"{opt_dir}/6-name2semantic.tsv","w",encoding="utf8") as f:    
            f.write("\n".join(opt)+"\n")
        os.remove(f"{opt_dir}/6-name2semantic-0.tsv")

# 2. finetuning
def finetuning(exp):
    opt_dir = f'{exp_root}/{exp["name"]}'

    os.makedirs(f"{opt_dir}/logs_s2_v3",exist_ok=True)

    # Perform same checks as webui
    assert os.path.exists(opt_dir)
    paths = ['2-name2text.txt', '4-cnhubert', '5-wav32k', '6-name2semantic.tsv']
    for f in paths:
        path = f"{opt_dir}/{f}"
        assert os.path.exists(path)
    
    phone_path, hubert_path, wav_path, semantic_path = path_list[1:]
    with open(phone_path,'r',encoding='utf-8') as f:
        assert f.read(1)
    assert os.listdir(hubert_path)
    assert os.listdir(wav_path)
    df = pd.read_csv(
        semantic_path, delimiter="\t", encoding="utf-8"
    )
    assert len(df) > 0

    # 1. SoVITS
    # (does 's2' stand for 'stage 2'?)
    with open("GPT_SoVITS/configs/s2.json","r",encoding="utf8") as f:
        config = json.load(f)

    config["train"]["fp16_run"] = is_half
    # The original script automatically sets the batch size to half if not using is_half
    # We won't do that here
    config["train"].update({
        "batch_size": SOVITS_BATCH_SIZE,
        "epochs": exp["sovits_epochs"],
        "text_low_lr_rate": SOVITS_LOW_LR_RATE,
        "pretrained_s2G": S2G_MODEL_DIR,
        # "pretrained_s2D": S2D_MODEL_DIR, # They did not release the discriminator; it's not used in finetuning
        "if_save_latest": True, # i.e. save only latest full checkpoint
        "if_save_every_weights": True, # i.e. small final model to weights at each savepoint as in RVC
        "save_every_epoch": SOVITS_SAVE_FREQUENCY,
        "gpu_numbers": "0",
        "grad_ckpt": False, # i.e. Gradient checkpointing - this is not visible in webUI and set to False by default (?)
        "lora_rank": exp["sovits_lora_rank"],
        "name": exp["name"],
        "version": "v3",
        "s2_ckpt_dir": opt_dir,
        "save_weight_dir": "SoVITS_weights_v3",
    })
    config["train"]["model"]["version"] = "v3"
    config["train"]["data"]["exp_dir"] = opt_dir

    tmp_config_path = f"{tmp_dir}/tmp_s2.json"
    with open(tmp_config_path,"w") as f:
        json.dump(config,f,indent=4)

    cmd = f"{python_exec} GPT_SoVITS/s2_train_v3_lora.py --config {tmp_config_path}"
    p = run(cmd, shell=True)

    # 2. GPT
    # (why did they switch to yaml?)
    with open("GPT_SoVITS/configs/s1longer-v2.yaml") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    os.makedirs(f"{opt_dir}/logs_s1",exist_ok=True)

    if is_half:
        config["train"]["precision"] = "16-mixed"
    else:
        config["train"]["precision"] = "32"
    config["train"]["batch_size"] = GPT_BATCH_SIZE
    config["train"]["epochs"] = exp["gpt_epochs"]
    config["pretrained_s1"] = GPT_MODEL_DIR
    config["train"]["save_every_n_epoch"] = GPT_SAVE_FREQUENCY
    config["train"]["if_save_every_weights"] = True
    config["train"]["if_save_latest"] = True
    config["train"]["if_dpo"] = True
    config["train"]["half_weights_save_dir"] = "GPT_weights_v3"
    config["train"]["exp_name"] = exp["name"]
    config["train_semantic_path"] = f"{opt_dir}/6-name2semantic.tsv"
    config["train_phoneme_path"] = f"{opt_dir}/2-name2text.txt"
    config["output_dir"] = f"{opt_dir}/logs_s1_{version}"

    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    os.environ["hz"] = "25hz" # ???

    tmp_config_path = f"{tmp_dir}/tmp_s1.yaml"
    with open(tmp_config_path,"w") as f:
        f.write(yaml.dump(config, default_flow_style=False))

    cmd = f"{python_exec} GPT_SoVITS/s1_train.py --config {tmp_config_path}"
    p = run(cmd, shell=True)

# %%
for exp in EXPS:
    print(exp["name"])
    print("Preprocessing dataset...")
    dataset_formatting(exp)
    print("Training...")
    train(exp)
# %%
