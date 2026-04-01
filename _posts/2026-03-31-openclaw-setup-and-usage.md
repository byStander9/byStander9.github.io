---
layout: post
title: "OpenClaw 설치 및 설정 기록"
date: 2026-03-31 20:47:00 +0900
categories: [openclaw, ubuntu, automation]
tags: [notion, gmail, discord]
summary: "Ubuntu에서 OpenClaw를 설치하고 onboard, Google Workspace, Notion, GitHub, Discord 준비까지 실제로 연결해 본 기록."
repo_url: "https://github.com/byStander9/openclaw-setup-playbook"
---

OpenClaw를 Ubuntu 환경에 설치하고, 초기 설정과 외부 서비스 연동까지 진행한 내용을 정리했다.
이 글은 사용 중 남긴 기록에 가깝고, 실제로 설정하면서 확인한 흐름과 문제 해결 과정을 중심으로 적었다.

## 3줄 요약

- Ubuntu 환경에서 OpenClaw를 설치하고 `openclaw onboard`로 초기 설정을 진행했다.
- Google Workspace, Notion, GitHub, Discord 관련 설정을 실제로 연결하고 동작 여부를 확인했다.
- 연동 과정에서 생긴 인증·환경변수·API 활성화 문제를 정리하고 해결했다.

## 설치 흐름

먼저 Ubuntu에서 기본 패키지를 설치했다.

```bash
sudo apt update && sudo apt install -y git curl build-essential
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs
npm install -g openclaw
openclaw help
```

그다음 초기 설정은 `openclaw onboard` 중심으로 진행했다.

```bash
openclaw onboard
```

개별 명령을 하나씩 맞추는 것보다 onboarding 흐름으로 시작하는 편이 훨씬 덜 헷갈렸다.

## 연동한 것들

실제로 연결하고 확인한 항목은 다음과 같다.

- Gmail
- Google Calendar
- Google Drive
- Notion
- GitHub CLI
- Discord 연동 준비

단순 인증만 한 것이 아니라 실제 메일 조회, 일정 조회, 문서 작성, 저장소 접근 확인까지 진행했다.

## 겪은 문제

### `gog` 키링 비밀번호 문제

비대화형 환경에서 `gog` 토큰을 읽지 못하는 문제가 있었다.
이 문제는 OpenClaw가 실행되는 서비스 환경에서 필요한 값을 읽지 못해서 발생했다.

해결은 `/etc/openclaw/openclaw.env`를 만들고, `GOG_KEYRING_PASSWORD`, `GOG_ACCOUNT`를 연결한 뒤 gateway를 재시작하는 방식으로 진행했다.

### Google Calendar API 비활성화

Calendar는 처음에 인증 문제가 아니라 API 활성화 문제로 막혔다.
Google Cloud Console에서 Calendar API를 활성화한 뒤 다시 조회하니 정상 동작했다.

## 메모

OpenClaw는 설치 자체보다도 실제로 어떤 서비스와 연결해 쓸 것인지, 그리고 그 연결이 비대화형 환경에서 안정적으로 유지되는지 확인하는 과정이 더 중요했다.

특히 다음이 중요했다.

- 서비스 환경과 사용자 셸 환경은 다를 수 있음
- API 활성화 여부는 인증과 별개 문제일 수 있음
- `openclaw onboard`를 중심에 두면 초반 설정 흐름이 단순해짐
- 실사용 테스트를 해봐야 설정이 끝났는지 알 수 있음
