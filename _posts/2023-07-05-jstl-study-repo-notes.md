---
layout: post
title: "Jstl_Study 개발 기록"
date: 2023-07-05 13:09:08 +0900
categories: ["repository", "java"]
tags: ["java", "jstl-study"]
summary: "Studying Jstl"
repo: "Jstl_Study"
repo_url: "https://github.com/byStander9/Jstl_Study"
generated: true
ai_enriched: false
---

Jstl_Study 레포를 기준으로 README와 파일 구조를 자동으로 확인해 정리한 개발 기록이다.
이 글은 레포가 업데이트되면 GitHub Actions를 통해 다시 생성될 수 있다.

## 레포 개요

- 레포 주소: <https://github.com/byStander9/Jstl_Study>
- 기본 브랜치: `main`
- 주요 언어: Java
- 최근 업데이트: 2023.07.05
- 설명: Studying Jstl

## README에서 확인한 내용

README의 주요 섹션은 다음과 같다.

- Jstl_Study

README에서 눈에 띄는 내용은 다음과 같다.

- Studying Jstl

## 파일 구조 메모

최상위에서 확인되는 주요 항목은 다음과 같다.

```text
.settings/
WebContent/
build/
src/
.classpath
.project
README.md
```

## 기술 스택 단서

레포 메타데이터와 설정 파일 기준으로는 다음 기술이 보인다.

- Java

## 우선 확인할 파일

- `README.md`: 프로젝트 소개와 사용법을 담은 문서
- `.settings/org.eclipse.wst.common.project.facet.core.xml`: 구현 흐름을 확인할 수 있는 코드/설정 파일
- `WebContent/frontcontroller_start.html`: 구현 흐름을 확인할 수 있는 코드/설정 파일
- `WebContent/jstl_start.html`: 구현 흐름을 확인할 수 있는 코드/설정 파일
- `WebContent/WEB-INF/web.xml`: 구현 흐름을 확인할 수 있는 코드/설정 파일
- `src/main/java/com/sw/controller/BookDTO.java`: 구현 흐름을 확인할 수 있는 코드/설정 파일

## 다시 볼 때의 체크포인트

1. README에 실행 방법과 필요한 환경 변수가 충분히 적혀 있는지 확인한다.
2. 핵심 코드가 어떤 파일에 모여 있는지 보고, 기능이 커졌다면 분리 기준을 정한다.
3. 의존성 파일을 기준으로 로컬 실행과 배포 흐름이 재현 가능한지 확인한다.
4. 블로그에 보여주고 싶지 않은 레포라면 `_data/repositories.json`의 `hidden_repositories`로 옮긴다.
