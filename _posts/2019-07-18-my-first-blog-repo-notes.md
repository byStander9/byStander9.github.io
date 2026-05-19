---
layout: post
title: "my-first-blog 개발 기록"
date: 2019-07-18 10:46:38 +0900
categories: ["repository", "python"]
tags: ["python", "my-first-blog"]
summary: "my-first-blog 레포의 README와 파일 구조를 기준으로 정리한 개발 기록."
repo: "my-first-blog"
repo_url: "https://github.com/byStander9/my-first-blog"
generated: true
ai_enriched: false
---

my-first-blog 레포를 기준으로 README와 파일 구조를 자동으로 확인해 정리한 개발 기록이다.
이 글은 레포가 업데이트되면 GitHub Actions를 통해 다시 생성될 수 있다.

## 레포 개요

- 레포 주소: <https://github.com/byStander9/my-first-blog>
- 기본 브랜치: `master`
- 주요 언어: Python
- 최근 업데이트: 2019.07.18
- 설명: my-first-blog 레포의 README와 파일 구조를 기준으로 정리한 개발 기록.

## README에서 확인한 내용

현재 README를 찾지 못했다. 나중에 설치 방법, 실행 방법, 핵심 기능을 README에 추가하면 이 글도 더 풍부해진다.

## 파일 구조 메모

최상위에서 확인되는 주요 항목은 다음과 같다.

```text
mysite/
.gitignore
```

## 기술 스택 단서

레포 메타데이터와 설정 파일 기준으로는 다음 기술이 보인다.

- Python

## 우선 확인할 파일

- `mysite/manage.py`: 구현 흐름을 확인할 수 있는 코드/설정 파일
- `mysite/blog/__init__.py`: 구현 흐름을 확인할 수 있는 코드/설정 파일
- `mysite/blog/admin.py`: 구현 흐름을 확인할 수 있는 코드/설정 파일
- `mysite/blog/apps.py`: 구현 흐름을 확인할 수 있는 코드/설정 파일
- `mysite/blog/models.py`: 구현 흐름을 확인할 수 있는 코드/설정 파일
- `mysite/blog/tests.py`: 구현 흐름을 확인할 수 있는 코드/설정 파일

## 다시 볼 때의 체크포인트

1. README에 실행 방법과 필요한 환경 변수가 충분히 적혀 있는지 확인한다.
2. 핵심 코드가 어떤 파일에 모여 있는지 보고, 기능이 커졌다면 분리 기준을 정한다.
3. 의존성 파일을 기준으로 로컬 실행과 배포 흐름이 재현 가능한지 확인한다.
4. 블로그에 보여주고 싶지 않은 레포라면 `_data/repositories.json`의 `hidden_repositories`로 옮긴다.
