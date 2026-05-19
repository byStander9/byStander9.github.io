---
layout: post
title: "gpt2_bible 개발 기록"
date: 2024-09-12 18:17:17 +0900
categories: ["repository", "python"]
tags: ["python", "gpt2-bible"]
summary: "training gpt2 model with bible dataset"
repo: "gpt2_bible"
repo_url: "https://github.com/byStander9/gpt2_bible"
generated: true
ai_enriched: false
---

gpt2_bible 레포를 기준으로 README와 파일 구조를 자동으로 확인해 정리한 개발 기록이다.
이 글은 레포가 업데이트되면 GitHub Actions를 통해 다시 생성될 수 있다.

## 레포 개요

- 레포 주소: <https://github.com/byStander9/gpt2_bible>
- 기본 브랜치: `main`
- 주요 언어: Python
- 최근 업데이트: 2024.09.12
- 설명: training gpt2 model with bible dataset

## README에서 확인한 내용

README의 주요 섹션은 다음과 같다.

- gpt2_bible

README에서 눈에 띄는 내용은 다음과 같다.

- training gpt2 model with bible dataset

## 파일 구조 메모

최상위에서 확인되는 주요 항목은 다음과 같다.

```text
README.md
bible_data.json
fine-tuning-gpt2.py
prompt.py
requirements.txt
```

## 기술 스택 단서

레포 메타데이터와 설정 파일 기준으로는 다음 기술이 보인다.

- Python

## 우선 확인할 파일

- `README.md`: 프로젝트 소개와 사용법을 담은 문서
- `fine-tuning-gpt2.py`: 구현 흐름을 확인할 수 있는 코드/설정 파일
- `prompt.py`: 구현 흐름을 확인할 수 있는 코드/설정 파일
- `requirements.txt`: 의존성과 실행 환경을 추정할 수 있는 설정 파일

## 다시 볼 때의 체크포인트

1. README에 실행 방법과 필요한 환경 변수가 충분히 적혀 있는지 확인한다.
2. 핵심 코드가 어떤 파일에 모여 있는지 보고, 기능이 커졌다면 분리 기준을 정한다.
3. 의존성 파일을 기준으로 로컬 실행과 배포 흐름이 재현 가능한지 확인한다.
4. 블로그에 보여주고 싶지 않은 레포라면 `_data/repositories.json`의 `hidden_repositories`로 옮긴다.
