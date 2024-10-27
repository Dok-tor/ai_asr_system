---
library_name: transformers
language:
- ru
license: apache-2.0
base_model: openai/whisper-small
tags:
- generated_from_trainer
datasets:
- mozilla-foundation/common_voice_11_0
metrics:
- wer
model-index:
- name: Whisper Small Ru
  results:
  - task:
      name: Automatic Speech Recognition
      type: automatic-speech-recognition
    dataset:
      name: Common Voice 11.0
      type: mozilla-foundation/common_voice_11_0
      config: ru
      split: test
      args: 'config: ru, split: test'
    metrics:
    - name: Wer
      type: wer
      value: 14.91770049819283
---

<!-- This model card has been generated automatically according to the information the Trainer had access to. You
should probably proofread and complete it, then remove this comment. -->

# Whisper Small Ru

This model is a fine-tuned version of [openai/whisper-small](https://huggingface.co/openai/whisper-small) on the Common Voice 11.0 dataset.
It achieves the following results on the evaluation set:
- Loss: 0.1877
- Wer: 14.9177

## Model description

More information needed

## Intended uses & limitations

More information needed

## Training and evaluation data

More information needed

## Training procedure

### Training hyperparameters

The following hyperparameters were used during training:
- learning_rate: 1e-05
- train_batch_size: 16
- eval_batch_size: 8
- seed: 42
- optimizer: Adam with betas=(0.9,0.999) and epsilon=1e-08
- lr_scheduler_type: linear
- lr_scheduler_warmup_steps: 500
- training_steps: 4000
- mixed_precision_training: Native AMP

### Training results

| Training Loss | Epoch  | Step | Validation Loss | Wer     |
|:-------------:|:------:|:----:|:---------------:|:-------:|
| 0.171         | 0.4924 | 1000 | 0.2239          | 18.2194 |
| 0.164         | 0.9847 | 2000 | 0.1985          | 16.0716 |
| 0.0697        | 1.4771 | 3000 | 0.1922          | 15.4696 |
| 0.0715        | 1.9695 | 4000 | 0.1877          | 14.9177 |


### Framework versions

- Transformers 4.45.1
- Pytorch 2.4.1+cu124
- Datasets 3.0.1
- Tokenizers 0.20.0
