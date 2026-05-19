---
layout: post
title: "rag-notebook-base 개발 기록"
date: 2026-05-14 20:02:38 +0900
categories: ["repository", "python"]
tags: ["python", "rag-notebook-base"]
summary: "PDF 또는 TXT 문서를 업로드하면, 업로드된 문서 내용만 근거로 질문에 답하는 로컬 단일 사용자용 RAG MVP입니다."
repo: "rag-notebook-base"
repo_url: "https://github.com/byStander9/rag-notebook-base"
generated: true
ai_enriched: false
---

rag-notebook-base 레포를 기준으로 README와 파일 구조를 자동으로 확인해 정리한 개발 기록이다.
이 글은 레포가 업데이트되면 GitHub Actions를 통해 다시 생성될 수 있다.

## 레포 개요

- 레포 주소: <https://github.com/byStander9/rag-notebook-base>
- 기본 브랜치: `main`
- 주요 언어: Python
- 최근 업데이트: 2026.05.14
- 설명: PDF 또는 TXT 문서를 업로드하면, 업로드된 문서 내용만 근거로 질문에 답하는 로컬 단일 사용자용 RAG MVP입니다.

## README에서 확인한 내용

README의 주요 섹션은 다음과 같다.

- RAG Notebook Base 한글 가이드
- 주요 기능
- Ubuntu / Linux 실행 방식
- Windows 실행 방식
- 실행 옵션

README에서 눈에 띄는 내용은 다음과 같다.

- PDF 또는 TXT 문서를 업로드하면, 업로드된 문서 내용만 근거로 질문에 답하는 로컬 단일 사용자용 RAG MVP입니다.
- 기본 흐름은 다음과 같습니다.
- 문서 업로드 -> 텍스트 추출 -> chunk 분할 -> embedding 생성 -> Chroma 저장
- -> 질문 입력 -> 관련 chunk 검색 -> LLM 답변 생성 -> 근거 chunk 표시
- PDF 텍스트 추출: PyMuPDF
- TXT 텍스트 추출: UTF-8, UTF-8 BOM, CP949 fallback
- 문자 단위 chunking
- Chroma 로컬 vector DB

## 파일 구조 메모

최상위에서 확인되는 주요 항목은 다음과 같다.

```text
data/
src/
.env.example
.gitignore
README.ko.md
README.md
app.py
pyproject.toml
requirements.txt
run.ps1
run.sh
uv.lock
```

## 기술 스택 단서

레포 메타데이터와 설정 파일 기준으로는 다음 기술이 보인다.

- Python

## 우선 확인할 파일

- `README.ko.md`: 프로젝트 소개와 사용법을 담은 문서
- `README.md`: 프로젝트 소개와 사용법을 담은 문서
- `app.py`: 구현 흐름을 확인할 수 있는 코드/설정 파일
- `pyproject.toml`: 의존성과 실행 환경을 추정할 수 있는 설정 파일
- `requirements.txt`: 의존성과 실행 환경을 추정할 수 있는 설정 파일
- `run.sh`: 구현 흐름을 확인할 수 있는 코드/설정 파일

## 다시 볼 때의 체크포인트

1. README에 실행 방법과 필요한 환경 변수가 충분히 적혀 있는지 확인한다.
2. 핵심 코드가 어떤 파일에 모여 있는지 보고, 기능이 커졌다면 분리 기준을 정한다.
3. 의존성 파일을 기준으로 로컬 실행과 배포 흐름이 재현 가능한지 확인한다.
4. 블로그에 보여주고 싶지 않은 레포라면 `_data/repositories.json`의 `hidden_repositories`로 옮긴다.
