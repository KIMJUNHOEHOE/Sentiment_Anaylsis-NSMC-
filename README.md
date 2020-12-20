# KoElectra_Sentiment_Anaylsis-NSMC-
Transformers library에 배포된 monologg님의 Koelectra 모델을 활용한 네이버리뷰 감성평가 모델

## 실행방법

0. src/final 폴더의 'friends모델_v3_roberta_submit_best.py' 복사
혹은 
https://colab.research.google.com/drive/1UO9wTMHJaZZcYeVLi0GU11ndiOfD7QqN?usp=sharing 실행
1. 구글 colab에서 실행하는 것을 권고(아래 방법은 구글 colab 실행 기준)
  - 로컬 사용시 version.txt에 있는 환경 모두 설치 및 scr code 내의 경로 모두 변경 필요
2. 구글 드라이브의 디렉토리와 Colab을 연동(colab 기준 코드 1~2번째 셀 실행)
3. raw data에 있는 'Friends' 폴더를 다운받아 구글 드라이브 'drive/MyDrive'경로에 설치
4. 구글 colab 런타임 유형 변경 > GPU환경
5. 모두 실행

## 모델별 실행결과
- src/final 폴더의 'friends모델_v3_roberta_submit_best.py' 가 가장 성능 우수
- src/trial 폴더의 기타 모델 성능은 아래와 

![image](https://user-images.githubusercontent.com/43465126/102692006-f0868a80-4253-11eb-870b-6be5fcb39d9d.png)


## 데이터 출처
- https://github.com/e9t/nsmc.git

## 참고 소스코드 및 문헌

#### Hugging Face BERT Chris McCormick의 오픈소스 
https://colab.research.google.com/drive/1PHv-IRLPCtv7oTcIGbsgZHqrB5LPvB7S#scrollTo=PGnlRWvkY-2c

#### 네이버 영화리뷰 감정분석 with Hugging Face BERT
https://colab.research.google.com/drive/1Xs99-e4g6KS5Alu7z9CnrWX0J_f5HBsQ#scrollTo=muU2kS2GCh4y

#### Hugging Face Transformers 공식 library
https://huggingface.co/transformers/_modules/transformers/models/electra/modeling_electra.html#ElectraModel

#### monologg님의 KoBERT모델
https://github.com/monologg/KoBERT-Transformers.git

#### SKT/Brain KoBERT모델
https://github.com/SKTBrain/KoBERT

#### S/W Membership json파일 불러오기
https://www.secmem.org/blog/2020/07/19/Sentiment-Analysis/
