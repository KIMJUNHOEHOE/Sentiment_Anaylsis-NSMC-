# -*- coding: utf-8 -*-
"""감성분석모델_v3_KoBERT_submit.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1cAsyVoa_XjHDasWz4YvQgxij7pjDji7b

## reference
### Hugging Face BERT Chris McCormick의 오픈소스 참고
https://colab.research.google.com/drive/1PHv-IRLPCtv7oTcIGbsgZHqrB5LPvB7S#scrollTo=PGnlRWvkY-2c

https://colab.research.google.com/drive/1Xs99-e4g6KS5Alu7z9CnrWX0J_f5HBsQ#scrollTo=muU2kS2GCh4y

### SKTBRAIN / KoBERT 참고
https://github.com/SKTBrain/KoBERT

### monologg님 github 참고
https://github.com/monologg/KoBERT-Transformers
"""

!pip install transformers

!pip install sentencepiece

# Commented out IPython magic to ensure Python compatibility.
!git clone https://github.com/monologg/KoBERT-Transformers.git
# %cd KoBERT-Transformers
!pip install -r requirements.txt
!pip install .

import sentencepiece as spm
from tokenization_kobert import KoBertTokenizer
from transformers import BertModel, AdamW, BertConfig
from transformers import get_linear_schedule_with_warmup
from keras.preprocessing.sequence import pad_sequences
from torch.utils.data import TensorDataset, DataLoader, RandomSampler, SequentialSampler
from keras.preprocessing.sequence import pad_sequences
from sklearn.model_selection import train_test_split
import torch
from torch import nn

import pandas as pd
import numpy as np
import random
import time
import datetime

# 깃헙에서 네이버 영화리뷰 감정분석 데이터 다운로드
!git clone https://github.com/e9t/nsmc.git

# 훈련셋 / 테스트셋 로드
train_data = pd.read_csv("nsmc/ratings_train.txt", sep='\t')
test_data = pd.read_csv("nsmc/ratings_test.txt", sep='\t')

# 150,000 훈련셋 / 50,000 테스트셋
print(train_data.shape)
print(test_data.shape)

# EDA, 긍정 1 / 부정 0
train_data.head(100)

# 문장, label 추출
sen_train = train_data['document']
labels_train = train_data['label'].values

sen_test = test_data['document']
labels_test = test_data['label'].values

"""### KoBERT baseline 모델 구축"""

# BERT input 형식으로 변환
# 네이버 영화리뷰의 경우 문장이 하나인 것이 대부분
sen_bert_train = []
for i in sen_train:
  x = "[CLS] " + str(i) + " [SEP]"
  sen_bert_train.append(x)

sen_bert_test = []
for i in sen_test:
  x = "[CLS] " + str(i) + " [SEP]"
  sen_bert_test.append(x)

# KoBERT 토크나이저로 문장 토큰 분리
tokenizer = KoBertTokenizer.from_pretrained('monologg/kobert') #KoBERT의 경우 setencepiece tokenizer
##Sentencepiece의 경우 빈도수를 기반으로 BPE를 수행하며
# Wordpiece의 경우 likelihood를 기반으로 BPE를 수행한 알고리즘
tokenized_texts_train = [tokenizer.tokenize(sent) for sent in sen_bert_train]
tokenized_texts_test = [tokenizer.tokenize(sent) for sent in sen_bert_test]

print(tokenized_texts_train[0])

print(tokenizer.all_special_ids)
print(tokenizer.all_special_tokens)

# BERT_Tokenizer vocab list(Kobert)
tokenizer.vocab_size

# Map the token strings to their vocabulary indeces.
indexed_tokens = tokenizer.convert_tokens_to_ids(tokenized_texts_train[0])

# Display the words with their indeces.
for tup in zip(tokenized_texts_train[0], indexed_tokens):
    print('{:<12} {:>6,}'.format(tup[0], tup[1]))

# 입력 토큰의 최대 시퀀스 길이 찾기
sen_len = [len(sen) for sen in sen_bert_train]
max(sen_len)

# Commented out IPython magic to ensure Python compatibility.
import matplotlib.pyplot as plt
# %matplotlib inline

plt.plot(sen_len)

# 토큰의 최대 시퀀스 길이
MAX_LEN = 160 # 대부분의 길이가 160 미만의 token
# 토큰을 숫자 인덱스로 변환
input_ids_train = [tokenizer.convert_tokens_to_ids(x) for x in tokenized_texts_train]
input_ids_test = [tokenizer.convert_tokens_to_ids(x) for x in tokenized_texts_test]

# 문장을 MAX_LEN 길이에 맞게 자르고, 모자란 부분을 패딩 1으로 채움, KoBERT의 경우 padding id=1
input_ids_train = pad_sequences(input_ids_train, maxlen=MAX_LEN, dtype="long", truncating="post", padding="post", value=1.0)
input_ids_test = pad_sequences(input_ids_test, maxlen=MAX_LEN, dtype="long", truncating="post", padding="post", value=1.0)

# 패딩 부분은 BERT 모델에서 어텐션을 수행하지 않아 속도 향상

# 어텐션 마스크 초기화
attention_masks_train = []
attention_masks_test = []

# 어텐션 마스크를 패딩이 아니면 1, 패딩이면 0으로 설정
for seq in input_ids_train: #Kobert에서는 패딩 id=1 / original bert에서는 패딩 id=0
    seq_mask = [float(i!=1) for i in seq]
    attention_masks_train.append(seq_mask)

for seq in input_ids_test:
    seq_mask = [float(i!=1) for i in seq]
    attention_masks_test.append(seq_mask)

# trainset, validation set 분리
train_inputs, validation_inputs, train_labels, validation_labels = train_test_split(input_ids_train,
                                                                                    labels_train, 
                                                                                    random_state=2020, 
                                                                                    test_size=0.3)

# 어텐션 마스크 분리
train_masks, validation_masks, _, _ = train_test_split(attention_masks_train, 
                                                       input_ids_train,
                                                       random_state=2020, 
                                                       test_size=0.3)

# 파이토치의 텐서로 변환
# train, validaiton set
train_inputs = torch.tensor(train_inputs)
train_labels = torch.tensor(train_labels,dtype=torch.long)
train_masks = torch.tensor(train_masks,dtype=torch.long)
validation_inputs = torch.tensor(validation_inputs)
validation_labels = torch.tensor(validation_labels,dtype=torch.long)
validation_masks = torch.tensor(validation_masks,dtype=torch.long)

# test set
test_inputs = torch.tensor(input_ids_test)
test_labels = torch.tensor(labels_test,dtype=torch.long)
test_masks = torch.tensor(attention_masks_test,dtype=torch.long)

# 배치 사이즈
batch_size = 32

# 파이토치의 DataLoader로 입력, 마스크, 라벨을 묶어 데이터 설정
# 학습시 배치 사이즈 만큼 데이터를 가져옴
train_tensor = TensorDataset(train_inputs, train_masks, train_labels)
train_sampler = RandomSampler(train_tensor)
train_dataloader = DataLoader(train_tensor, sampler=train_sampler, batch_size=batch_size)

validation_tensor = TensorDataset(validation_inputs, validation_masks, validation_labels)
validation_sampler = SequentialSampler(validation_tensor)
validation_dataloader = DataLoader(validation_tensor, sampler=validation_sampler, batch_size=batch_size)

test_data = TensorDataset(test_inputs, test_masks, test_labels)
test_sampler = RandomSampler(test_data)
test_dataloader = DataLoader(test_data, sampler=test_sampler, batch_size=batch_size)

"""### 모델생성"""

# GPU 사용 확인
!nvidia-smi

# 디바이스 설정
if torch.cuda.is_available():    
    device = torch.device("cuda")
    print('There are %d GPU(s) available.' % torch.cuda.device_count())
    print('We will use the GPU:', torch.cuda.get_device_name(0))
else:
    device = torch.device("cpu")
    print('No GPU available, using the CPU instead.')

class SentimentClassifier(nn.Module):
  def __init__(self, n_classes):
    super(SentimentClassifier, self).__init__()
    self.bert = BertModel.from_pretrained('monologg/kobert',return_dict=False)
    self.drop = nn.Dropout(p=0.1)
    self.out = nn.Linear(self.bert.config.hidden_size, n_classes)

  def forward(self, input_ids, attention_mask):
    _, pooled_output = self.bert(
      input_ids=input_ids,
      attention_mask=attention_mask
    )
    output = self.drop(pooled_output)
    return self.out(output)

# 분류 BERT 모델 생성
model = SentimentClassifier(2) # label은 0,1 class 2개
model = model.to(device)

# 옵티마이저 설정
optimizer = AdamW(model.parameters(),
                  lr = 2e-5, # 학습률
                  eps = 1e-8 # 0으로 나누는 것을 방지하기 위한 epsilon 값
                )

# 에폭수
epochs = 4

# 총 훈련 스텝 : 배치반복 횟수 * 에폭
total_steps = len(train_dataloader) * epochs

# 처음에 학습률을 조금씩 변화시키는 스케줄러 생성
scheduler = get_linear_schedule_with_warmup(optimizer, 
                                            num_warmup_steps = 0,
                                            num_training_steps = total_steps)
# 손실함수 설정
loss_fn = torch.nn.CrossEntropyLoss().to(device) #logits을 softmax 자동 취함

# 정확도 계산 함수
def flat_accuracy(preds, labels):
    
    pred_flat = np.argmax(preds, axis=1).flatten()
    labels_flat = labels.flatten()

    return np.sum(pred_flat == labels_flat) / len(labels_flat)

# 시간 표시 함수
def format_time(elapsed):

    # 반올림
    elapsed_rounded = int(round((elapsed)))
    
    # hh:mm:ss으로 형태 변경
    return str(datetime.timedelta(seconds=elapsed_rounded))

# 그래디언트 초기화
model.zero_grad()

# 에폭만큼 반복
for epoch_i in range(0, epochs):
    
    # ========================================
    #               Training
    # ========================================
    
    print("")
    print('======== Epoch {:} / {:} ========'.format(epoch_i + 1, epochs))
    print('Training...')

    # 시작 시간 설정
    t0 = time.time()

    # 로스 초기화
    total_loss = 0

    # 훈련모드로 변경
    model.train()
        
    # 데이터로더에서 배치만큼 반복하여 가져옴 - 배치사이즈가 클 경우 out of memory 문제
    for step, batch in enumerate(train_dataloader):
        # 단순 경과 정보 표시, 실제 BERT학습은 32 batch size씩, iteration : 3282
        if step % 500 == 0 and not step == 0:
            elapsed = format_time(time.time() - t0)
            print('  Step {:>5,}  of  {:>5,}.    Elapsed: {:}.'.format(step, len(train_dataloader), elapsed))

        # 배치를 GPU에 넣음
        batch = tuple(t.to(device) for t in batch)
        
        # 배치에서 데이터 추출
        b_input_ids, b_input_mask, b_labels = batch

        # Forward 수행                
        outputs = model(b_input_ids, 
                        attention_mask=b_input_mask
                        )
        
        loss = loss_fn(outputs, b_labels)

        # 총 로스 계산
        total_loss += loss.item()

        # Backward 수행으로 그래디언트 계산
        loss.backward()

        # 그래디언트 클리핑
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

        # 그래디언트를 통해 가중치 파라미터 업데이트
        optimizer.step()

        # 스케줄러로 학습률 감소
        scheduler.step()

        # 그래디언트 초기화
        model.zero_grad()

    # 평균 로스 계산
    avg_train_loss = total_loss / len(train_dataloader)            

    print("")
    print("  Average training loss: {0:.4f}".format(avg_train_loss))
    print("  Training epcoh took: {:}".format(format_time(time.time() - t0)))
        
    # ========================================
    #               Validation
    # ========================================

    print("")
    print("Running Validation...")

    #시작 시간 설정
    t0 = time.time()

    # 평가모드로 변경
    model.eval()

    # 변수 초기화
    eval_loss, eval_accuracy = 0, 0
    nb_eval_steps, nb_eval_examples = 0, 0

    # 데이터로더에서 배치만큼 반복하여 가져옴
    for batch in validation_dataloader:
        # 배치를 GPU에 넣음
        batch = tuple(t.to(device) for t in batch)
        
        # 배치에서 데이터 추출
        b_input_ids, b_input_mask, b_labels = batch
        
        # 그래디언트 계산 안함
        with torch.no_grad():     
            # Forward 수행
            outputs = model(b_input_ids, 
                            attention_mask=b_input_mask)
        
        # 로짓 구함
        logits = outputs

        # CPU로 데이터 이동
        logits = logits.detach().cpu().numpy()
        label_ids = b_labels.to('cpu').numpy()
        
        # 출력 로짓과 라벨을 비교하여 정확도 계산
        tmp_eval_accuracy = flat_accuracy(logits, label_ids)
        eval_accuracy += tmp_eval_accuracy
        nb_eval_steps += 1

    print("  Accuracy: {0:.4f}".format(eval_accuracy/nb_eval_steps))
    print("  Validation took: {:}".format(format_time(time.time() - t0)))

print("")
print("Training complete!")

"""### 테스트셋 평가"""

#시작 시간 설정
t0 = time.time()

# 평가모드로 변경
model.eval()

# 변수 초기화
eval_loss, eval_accuracy = 0, 0
nb_eval_steps, nb_eval_examples = 0, 0

# 데이터로더에서 배치만큼 반복하여 가져옴
for step, batch in enumerate(test_dataloader):
    # 경과 정보 표시
    if step % 100 == 0 and not step == 0:
        elapsed = format_time(time.time() - t0)
        print('  Step {:>5,}  of  {:>5,}.    Elapsed: {:}.'.format(step, len(test_dataloader), elapsed))

    # 배치를 GPU에 넣음
    batch = tuple(t.to(device) for t in batch)
    
    # 배치에서 데이터 추출
    b_input_ids, b_input_mask, b_labels = batch
    
    # 그래디언트 계산 안함
    with torch.no_grad():     
        # Forward 수행
        outputs = model(b_input_ids,  
                        attention_mask=b_input_mask)
    
    # 로짓 구함
    logits = outputs

    # CPU로 데이터 이동
    logits = logits.detach().cpu().numpy()
    label_ids = b_labels.to('cpu').numpy()
    
    # 출력 로짓과 라벨을 비교하여 정확도 계산
    tmp_eval_accuracy = flat_accuracy(logits, label_ids)
    eval_accuracy += tmp_eval_accuracy
    nb_eval_steps += 1

print("")
print("Accuracy: {0:.4f}".format(eval_accuracy/nb_eval_steps))
print("Test took: {:}".format(format_time(time.time() - t0)))