# What is this?
Implements a GUI for GPT-SoVITS.

![Overall GUI](/../standalone_gui/docs/screenshots/overall.png)

Features:
- Reference audio management
  * Pony Preservation Project format filename parsing
  * Builtin downloader for Clipper's Master File
- Add models from a huggingface repo in the GUI
- Parallelized repeated generations 
- Rich audio preview with drag and drop
- Experimental custom ARPAbet support (english only)
  * Type in ARPAbet in curly braces, e.g. `{D IH0 S P EH1 N S ER0}`
  * Vowel stress numbers are required.
- Bugfixes to the original repo (invalidating cache for change in prompt lang)

# Instructions 
An NVIDIA GPU is recommended. You can get away with 4 GB VRAM but higher is better. CPU-only inference is possible, but slow (~9x slower).

## Installation
### ffmpeg
GPT-SoVITS depends on FFmpeg, which is bundled with the Windows pyinstaller. If using from source, follow the below instructions:

#### Conda Users
```bash
conda install ffmpeg
```

#### Ubuntu/Debian Users
```bash
sudo apt install ffmpeg
sudo apt install libsox-dev
```

#### Windows Users
Download and place [ffmpeg.exe](https://huggingface.co/lj1995/VoiceConversionWebUI/blob/main/ffmpeg.exe) and [ffprobe.exe](https://huggingface.co/lj1995/VoiceConversionWebUI/blob/main/ffprobe.exe) in the GPT-SoVITS root.

Install [Visual Studio 2017](https://aka.ms/vs/17/release/vc_redist.x86.exe) (Korean TTS Only)

#### MacOS Users
```bash
brew install ffmpeg
```

### From pyinstaller (Windows)
The pyinstaller build uses approx. 10 GB of disk space including pretrained models bundled with it. As this is too large for GitHub, the latest release is hosted [here](https://drive.google.com/file/d/1dgG1kg0e9p4khrwpPaI9NdV_PIiMDGOZ/view) and can be run simply by executing `gptsovits.exe`. The client will automatically download the necessary pretrained models for inference on startup.

Also see: [Build folder](https://drive.google.com/drive/folders/141YfYH_GS29D80kAcKljmXgN91zKLbUq)
[CPU-only pytorch version](https://drive.google.com/file/d/1FVuwuKyUqfuRcHVKr-ACgAul4araUjPN/view?usp=drive_link)

### From source (other) (recommend python=3.10)
1. Clone the repository. 
  * Set up a conda environment if you wish: `conda create -n GPTSovitsClient python=3.10`
    - Activate the environment: `conda activate GPTSovitsClient`
  * Or set up a venv if you wish: `python -m venv GPTSovitsClient`
    - Activate the environment (Unix/MacOS): `source GPTSovitsClient/bin/activate`
    - Activate the environment (Windows): `GPTSovitsClient\Scripts\activate`
2. Install pytorch 2.3.0: `pip install torch==2.3.0 torchvision==0.18.0 torchaudio==2.3.0 --index-url https://download.pytorch.org/whl/cu118`
3. `pip install -r requirements.txt -r requirements_client.txt`
4. Then launch the server with `python gui_client.py`. The client will automatically download the necessary pretrained models for inference on startup.

### Troubleshooting
- On Windows -- if audio playback fails mentioning `DirectShowPlayerService error`, this is a codec issue. Try installing [K-Lite Codecs](https://codecguide.com/download_kl.htm).
- On Linux: The GUI uses the PyQt5 multimedia library and gstreamer which may not be installed on your distro.
  - On Ubuntu or other apt distros, try `apt install libqt5multimedia5 libgstreamer1.0-dev libgstreamer-plugins-bad1.0-dev libgstreamer-plugins-base1.0-dev libgstreamer-plugins-good1.0-dev`
  - If not using apt, try to find and install the equivalent packages for your distro.
- `RuntimeError: Failed to load Audio`. This is because ffmpeg could not be detected on your system. Ensure that ffmpeg is installed according to the provided instructions above.

## DPI scaling
- If you are using a high DPI monitor, run the program first. A config file called `effusive_gui_config.yaml` will appear.
- Set `enable_hi_dpi` to `True`.

## Usage
- **Starting the program.** Be patient -- there's a lot of Python in there! It takes me minimum 10 seconds to start seeing console output.
### Adding models. 
By default, the pyinstaller version comes "batteries included" with Mane 6 voices for TTS, but it will only have the base GPT-SoVITS model if you opted for a source install. You may be interested in downloading other models from a huggingface repo. This can be done from within the interface by clicking on the **Add Model** action in the toolbar. Typically, each model occupies ~220 MB of disk space.

1. Specify the huggingface repo id in `HF Repo:` and hit enter.
2. Select the desired model to download.
3. Click `add to server` and wait for the model to download.

![Adding models](/../standalone_gui/docs/screenshots/addmodel.png)

- Currently, this tool expects the huggingface repo to be laid out in a certain way; see [this repo](https://huggingface.co/therealvul/GPT-SoVITS-v2) for an example. I did not use `.zip` because it can obscure the directory structure.
- Models downloaded this way are placed in the `models` directory which is created if it does not exist.
- (pyinstaller) You can also manually add "loose" models (i.e. models not coupled to any particular character) by creating `GPT_weights_v2` and `SoVITS_weights_v2` directories next to the .exe and placing the weights in those respective directories.

### Model selection
*Note that the initial model when the GUI is first loaded is the base model, which is not finetuned on any particular characters. Download and load a more specific model for better results.*

Under this section, you can select either individual weights or speaker-bundled weights (i.e. paired GPT and SoVITS weights corresponding to a particular speaker, typically downloaded using the above `Add Model` action and located in the `models` directory.). 

![Selecting models](/../standalone_gui/docs/screenshots/selectmodel.png)

- To load the selected model, you must click `Load selected models`. 
- You can refresh the lists of available models from your filesystem by clicking `Refresh available models`.

### Reference audios
GPT-SoVITS accepts reference audio clips which can be used to control the intonation and timbre of the resulting generated speech. The Reference Audios section allows for the inputting, labeling, organization, and selection of reference audio for your generations. If you wish to download reference audio clips from Clipper's Master File, click the `Master file downloader` option at the top of the screen (see section `Master File Downloader` for more info)

![Reference audios](/../standalone_gui/docs/screenshots/refaudios.png)

- **One "required" field you must fill out for generation is `Utterance`,** which you should fill with a transcription of what is spoken in the reference audio.
- **One primary reference audio must be selected for generation.** The primary reference audio tends to control more overall pitch and intonation over timbre, while the aux reference audios have more control over timbre.
- All other editable fields and filters are purely for organization purposes.
- Audio following the PPP dataset naming format, e.g. `00_03_24_Pinkie_Happy_Noisy_There's a chance i may have missed a note or two Here or there, but i just love playing so much!.flac`, will automatically have their data fields filled out by parsing the file name.
- (pyinstaller) The pyinstaller build, in addition to the Mane 6 models, also comes with corresponding [reference audios](https://drive.google.com/file/d/1EljbxeUckYATH269utj7q1T-8oKcPhte/view?usp=drive_link) that can produce reasonable quality generations.

### Inference
The words to be spoken can be filled out under **Text prompt**. When ready to submit, click the **Generate** button to begin generation. Generations will appear under the **Generations** section, which can be previewed. In addition, you can drag and drop the resulting generated audio files from the play button icon into other programs.

- The audio is outputted in an `outputs` directory by default.
- The audio waveform preview supports drag+click to seek and spacebar to toggle playback.

![Inference](/../standalone_gui/docs/screenshots/inference.png)

- **Repetitions** can be used to generate, in parallel, multiple versions of the same prompt text, each of which will be displayed in the Generations section.
  * This is particularly useful for content creation purposes where you may be editing together multiple audio clips and looking for generations with specific inflections or other characteristics.
  * Setting a fixed seed for multiple repetitions is pointless (they will all be the same).
- A notable parameter for controlling memory usage is **batch size**. Higher batch sizes will result in higher maximum memory usage.
  * GPT-SoVITS only uses as many batches as it needs--so with a small number of batches and a low number of repetitions, your memory usage may not reflect the maximum amount of memory usage possible for a particular batch size.

### Master file downloader
The Master file downloader offers a basic interface to search and download reference audio files from Clipper's Master File. To do this it must first build an index of the available files; depending on network speed this can take anywhere from 20 seconds to multiple minutes.

![Master file downloader](/../standalone_gui/docs/screenshots/masterfile.png)

The `Glob search` field accepts glob-style filename patterns, i.e. `*_Rarity_*`. `Sort`
allows you to sort by file length. `Rebuild master file index` can be used to rebuild the index, which can be useful if the Master File is updated in the future.

# Building
A conda environment appropriately set up to run the client, plus pyinstaller, on Windows, should allow you to run `pyinstaller gptsovits_client.spec` which should reproduce the pyinstaller (minus bundled reference audios and models).

# FAQ
* **Why is Twilight Sparkle underneath the drag and drop cursor?** Because PyQt5 starts screaming into the console if the drag pixmap is nothing.
* **Why am I running out of memory?** Very long sentences and using too high of a batch size can both increase your VRAM usage; consider lowering them according to your available GPU resources.
  - **Text split** applies directly to this. For example, "batch every 4 sentences" will result in longer items per batch increasing overall VRAM usage.
  - Higher `n_repetitions` can "fill out" batches more quickly, but the limiting factor should still be batch size.
* **Why is interrupt spotty?** Internally the way GPT-SoVITS has implemented this is just by setting a flag that's checked in the middle of generation. I'm not sure if there's a more robust way to interrupt the generation process.
* **Why is the text prompt area so small?** It is to discourage you from using excessively long prompts which could trigger OOM issues, since I don't have a robust way of dealing with OOM right now. But you are allowed to type/paste in as much text as you think you want.

#### Install FFmpeg

##### Conda Users

```bash
conda install ffmpeg
```

##### Ubuntu/Debian Users

```bash
sudo apt install ffmpeg
sudo apt install libsox-dev
conda install -c conda-forge 'ffmpeg<7'
```

##### Windows Users

Download and place [ffmpeg.exe](https://huggingface.co/lj1995/VoiceConversionWebUI/blob/main/ffmpeg.exe) and [ffprobe.exe](https://huggingface.co/lj1995/VoiceConversionWebUI/blob/main/ffprobe.exe) in the GPT-SoVITS root.

Install [Visual Studio 2017](https://aka.ms/vs/17/release/vc_redist.x86.exe) (Korean TTS Only)

##### MacOS Users
```bash
brew install ffmpeg
```

#### Install Dependences

```bash
pip install -r requirements.txt
```

### Using Docker

#### docker-compose.yaml configuration

0. Regarding image tags: Due to rapid updates in the codebase and the slow process of packaging and testing images, please check [Docker Hub](https://hub.docker.com/r/breakstring/gpt-sovits) for the currently packaged latest images and select as per your situation, or alternatively, build locally using a Dockerfile according to your own needs.
1. Environment Variables：
   - is_half: Controls half-precision/double-precision. This is typically the cause if the content under the directories 4-cnhubert/5-wav32k is not generated correctly during the "SSL extracting" step. Adjust to True or False based on your actual situation.
2. Volumes Configuration，The application's root directory inside the container is set to /workspace. The default docker-compose.yaml lists some practical examples for uploading/downloading content.
3. shm_size： The default available memory for Docker Desktop on Windows is too small, which can cause abnormal operations. Adjust according to your own situation.
4. Under the deploy section, GPU-related settings should be adjusted cautiously according to your system and actual circumstances.

#### Running with docker compose

```
docker compose -f "docker-compose.yaml" up -d
```

#### Running with docker command

As above, modify the corresponding parameters based on your actual situation, then run the following command:

```
docker run --rm -it --gpus=all --env=is_half=False --volume=G:\GPT-SoVITS-DockerTest\output:/workspace/output --volume=G:\GPT-SoVITS-DockerTest\logs:/workspace/logs --volume=G:\GPT-SoVITS-DockerTest\SoVITS_weights:/workspace/SoVITS_weights --workdir=/workspace -p 9880:9880 -p 9871:9871 -p 9872:9872 -p 9873:9873 -p 9874:9874 --shm-size="16G" -d breakstring/gpt-sovits:xxxxx
```

## Pretrained Models

**Users in China can [download all these models here](https://www.yuque.com/baicaigongchang1145haoyuangong/ib3g1e/dkxgpiy9zb96hob4#nVNhX).**

1. Download pretrained models from [GPT-SoVITS Models](https://huggingface.co/lj1995/GPT-SoVITS) and place them in `GPT_SoVITS/pretrained_models`.

2. Download G2PW models from [G2PWModel_1.1.zip](https://paddlespeech.bj.bcebos.com/Parakeet/released_models/g2p/G2PWModel_1.1.zip), unzip and rename to `G2PWModel`, and then place them in `GPT_SoVITS/text`.(Chinese TTS Only)

3. For UVR5 (Vocals/Accompaniment Separation & Reverberation Removal, additionally), download models from [UVR5 Weights](https://huggingface.co/lj1995/VoiceConversionWebUI/tree/main/uvr5_weights) and place them in `tools/uvr5/uvr5_weights`.

    - If you want to use `bs_roformer` or `mel_band_roformer` models for UVR5, you can manually download the model and corresponding configuration file, and put them in `tools/uvr5/uvr5_weights`. **Rename the model file and configuration file, ensure that the model and configuration files have the same and corresponding names except for the suffix**. In addition, the model and configuration file names **must include `roformer`** in order to be recognized as models of the roformer class.

    - The suggestion is to **directly specify the model type** in the model name and configuration file name, such as `mel_mand_roformer`, `bs_roformer`. If not specified, the features will be compared from the configuration file to determine which type of model it is. For example, the model `bs_roformer_ep_368_sdr_12.9628.ckpt` and its corresponding configuration file `bs_roformer_ep_368_sdr_12.9628.yaml` are a pair, `kim_mel_band_roformer.ckpt` and `kim_mel_band_roformer.yaml` are also a pair.

4. For Chinese ASR (additionally), download models from [Damo ASR Model](https://modelscope.cn/models/damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch/files), [Damo VAD Model](https://modelscope.cn/models/damo/speech_fsmn_vad_zh-cn-16k-common-pytorch/files), and [Damo Punc Model](https://modelscope.cn/models/damo/punc_ct-transformer_zh-cn-common-vocab272727-pytorch/files) and place them in `tools/asr/models`.

5. For English or Japanese ASR (additionally), download models from [Faster Whisper Large V3](https://huggingface.co/Systran/faster-whisper-large-v3) and place them in `tools/asr/models`. Also, [other models](https://huggingface.co/Systran) may have the similar effect with smaller disk footprint.

## Dataset Format

The TTS annotation .list file format:

```
vocal_path|speaker_name|language|text
```

Language dictionary:

- 'zh': Chinese
- 'ja': Japanese
- 'en': English
- 'ko': Korean
- 'yue': Cantonese

Example:

```
D:\GPT-SoVITS\xxx/xxx.wav|xxx|en|I like playing Genshin.
```

## Finetune and inference

### Open WebUI

#### Integrated Package Users

Double-click `go-webui.bat`or use `go-webui.ps1`
if you want to switch to V1,then double-click`go-webui-v1.bat` or use `go-webui-v1.ps1`

#### Others

```bash
python webui.py <language(optional)>
```

if you want to switch to V1,then

```bash
python webui.py v1 <language(optional)>
```
Or maunally switch version in WebUI

### Finetune

#### Path Auto-filling is now supported

    1. Fill in the audio path
    2. Slice the audio into small chunks
    3. Denoise(optinal)
    4. ASR
    5. Proofreading ASR transcriptions
    6. Go to the next Tab, then finetune the model

### Open Inference WebUI

#### Integrated Package Users

Double-click `go-webui-v2.bat` or use `go-webui-v2.ps1` ,then open the inference webui at  `1-GPT-SoVITS-TTS/1C-inference`

#### Others

```bash
python GPT_SoVITS/inference_webui.py <language(optional)>
```
OR

```bash
python webui.py
```
then open the inference webui at `1-GPT-SoVITS-TTS/1C-inference`

## V2 Release Notes

New Features:

1. Support Korean and Cantonese

2. An optimized text frontend

3. Pre-trained model extended from 2k hours to 5k hours

4. Improved synthesis quality for low-quality reference audio

    [more details](https://github.com/RVC-Boss/GPT-SoVITS/wiki/GPT%E2%80%90SoVITS%E2%80%90v2%E2%80%90features-(%E6%96%B0%E7%89%B9%E6%80%A7))

Use v2 from v1 environment:

1. `pip install -r requirements.txt` to update some packages

2. Clone the latest codes from github.

3. Download v2 pretrained models from [huggingface](https://huggingface.co/lj1995/GPT-SoVITS/tree/main/gsv-v2final-pretrained) and put them into `GPT_SoVITS\pretrained_models\gsv-v2final-pretrained`.

    Chinese v2 additional: [G2PWModel_1.1.zip](https://paddlespeech.bj.bcebos.com/Parakeet/released_models/g2p/G2PWModel_1.1.zip)（Download G2PW models,  unzip and rename to `G2PWModel`, and then place them in `GPT_SoVITS/text`.

## V3 Release Notes

New Features:

1. The timbre similarity is higher, requiring less training data to approximate the target speaker (the timbre similarity is significantly improved using the base model directly without fine-tuning).

2. GPT model is more stable, with fewer repetitions and omissions, and it is easier to generate speech with richer emotional expression.

    [more details](https://github.com/RVC-Boss/GPT-SoVITS/wiki/GPT%E2%80%90SoVITS%E2%80%90v3%E2%80%90features-(%E6%96%B0%E7%89%B9%E6%80%A7))

Use v3 from v2 environment:

1. `pip install -r requirements.txt` to update some packages

2. Clone the latest codes from github.

3. Download v3 pretrained models (s1v3.ckpt, s2Gv3.pth and models--nvidia--bigvgan_v2_24khz_100band_256x folder) from [huggingface](https://huggingface.co/lj1995/GPT-SoVITS/tree/main) and put them into `GPT_SoVITS\pretrained_models`.

    additional: for Audio Super Resolution model, you can read [how to download](./tools/AP_BWE_main/24kto48k/readme.txt)


## Todo List

- [x] **High Priority:**

  - [x] Localization in Japanese and English.
  - [x] User guide.
  - [x] Japanese and English dataset fine tune training.

- [ ] **Features:**
  - [x] Zero-shot voice conversion (5s) / few-shot voice conversion (1min).
  - [x] TTS speaking speed control.
  - [ ] ~~Enhanced TTS emotion control.~~ Maybe use pretrained finetuned preset GPT models for better emotion.
  - [ ] Experiment with changing SoVITS token inputs to probability distribution of GPT vocabs (transformer latent).
  - [x] Improve English and Japanese text frontend.
  - [ ] Develop tiny and larger-sized TTS models.
  - [x] Colab scripts.
  - [x] Try expand training dataset (2k hours -> 10k hours).
  - [x] better sovits base model (enhanced audio quality)
  - [ ] model mix

## (Additional) Method for running from the command line
Use the command line to open the WebUI for UVR5
```
python tools/uvr5/webui.py "<infer_device>" <is_half> <webui_port_uvr5>
```
<!-- If you can't open a browser, follow the format below for UVR processing,This is using mdxnet for audio processing
```
python mdxnet.py --model --input_root --output_vocal --output_ins --agg_level --format --device --is_half_precision
``` -->
This is how the audio segmentation of the dataset is done using the command line
```
python audio_slicer.py \
    --input_path "<path_to_original_audio_file_or_directory>" \
    --output_root "<directory_where_subdivided_audio_clips_will_be_saved>" \
    --threshold <volume_threshold> \
    --min_length <minimum_duration_of_each_subclip> \
    --min_interval <shortest_time_gap_between_adjacent_subclips>
    --hop_size <step_size_for_computing_volume_curve>
```
This is how dataset ASR processing is done using the command line(Only Chinese)
```
python tools/asr/funasr_asr.py -i <input> -o <output>
```
ASR processing is performed through Faster_Whisper(ASR marking except Chinese)

(No progress bars, GPU performance may cause time delays)
```
python ./tools/asr/fasterwhisper_asr.py -i <input> -o <output> -l <language> -p <precision>
```
A custom list save path is enabled

## Credits

Special thanks to the following projects and contributors:

### Theoretical Research
- [ar-vits](https://github.com/innnky/ar-vits)
- [SoundStorm](https://github.com/yangdongchao/SoundStorm/tree/master/soundstorm/s1/AR)
- [vits](https://github.com/jaywalnut310/vits)
- [TransferTTS](https://github.com/hcy71o/TransferTTS/blob/master/models.py#L556)
- [contentvec](https://github.com/auspicious3000/contentvec/)
- [hifi-gan](https://github.com/jik876/hifi-gan)
- [fish-speech](https://github.com/fishaudio/fish-speech/blob/main/tools/llama/generate.py#L41)
- [f5-TTS](https://github.com/SWivid/F5-TTS/blob/main/src/f5_tts/model/backbones/dit.py)
- [shortcut flow matching](https://github.com/kvfrans/shortcut-models/blob/main/targets_shortcut.py)
### Pretrained Models
- [Chinese Speech Pretrain](https://github.com/TencentGameMate/chinese_speech_pretrain)
- [Chinese-Roberta-WWM-Ext-Large](https://huggingface.co/hfl/chinese-roberta-wwm-ext-large)
- [BigVGAN](https://github.com/NVIDIA/BigVGAN)
### Text Frontend for Inference
- [paddlespeech zh_normalization](https://github.com/PaddlePaddle/PaddleSpeech/tree/develop/paddlespeech/t2s/frontend/zh_normalization)
- [split-lang](https://github.com/DoodleBears/split-lang)
- [g2pW](https://github.com/GitYCC/g2pW)
- [pypinyin-g2pW](https://github.com/mozillazg/pypinyin-g2pW)
- [paddlespeech g2pw](https://github.com/PaddlePaddle/PaddleSpeech/tree/develop/paddlespeech/t2s/frontend/g2pw)
### WebUI Tools
- [ultimatevocalremovergui](https://github.com/Anjok07/ultimatevocalremovergui)
- [audio-slicer](https://github.com/openvpi/audio-slicer)
- [SubFix](https://github.com/cronrpc/SubFix)
- [FFmpeg](https://github.com/FFmpeg/FFmpeg)
- [gradio](https://github.com/gradio-app/gradio)
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [FunASR](https://github.com/alibaba-damo-academy/FunASR)
- [AP-BWE](https://github.com/yxlu-0102/AP-BWE)

Thankful to @Naozumi520 for providing the Cantonese training set and for the guidance on Cantonese-related knowledge.

## Thanks to all contributors for their efforts

<a href="https://github.com/RVC-Boss/GPT-SoVITS/graphs/contributors" target="_blank">
  <img src="https://contrib.rocks/image?repo=RVC-Boss/GPT-SoVITS" />
</a>
