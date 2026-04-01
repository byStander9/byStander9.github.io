---
layout: home
title: Home
---

<section class="home-hero hero-split">
  <div>
    <p class="home-kicker">BYSTANDER'S BLOG</p>
    <h1>기술 메모와 개발 기록</h1>
    <p>
      설치 기록, 실험 로그, 프로젝트 개발 내용을 정리하는 개인 블로그.
      실제로 사용해 본 내용과 개발 과정에서 정리해둘 만한 메모를 담는다.
    </p>
  </div>
  <div class="hero-panel">
    <div class="hero-panel-item">
      <span class="hero-panel-label">Posts</span>
      <strong>{{ site.posts | size }}</strong>
    </div>
    <div class="hero-panel-item">
      <span class="hero-panel-label">Categories</span>
      <strong>{{ site.categories | size }}</strong>
    </div>
    <div class="hero-panel-item">
      <span class="hero-panel-label">Tags</span>
      <strong>{{ site.tags | size }}</strong>
    </div>
  </div>
</section>

<section class="section-block compact-links">
  <div class="section-heading-row">
    <h2 class="section-heading">Featured Repositories</h2>
    <span class="section-subtle">레포 바로가기</span>
  </div>

  <div class="home-links repo-grid">
    <a href="https://github.com/byStander9/openclaw-setup-playbook">
      <strong>openclaw-setup-playbook</strong>
      <span>OpenClaw 설치와 연동 기록</span>
    </a>
    <a href="https://github.com/byStander9/discordBot">
      <strong>discordBot</strong>
      <span>Python 기반 Discord 음악 봇</span>
    </a>
  </div>
</section>
