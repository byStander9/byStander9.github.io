---
layout: page
title: Repositories
permalink: /repositories/
---

{% assign repos = site.data.repositories_generated %}
{% assign featured_repos = repos | where: "status", "featured" %}
{% assign published_repos = repos | where: "status", "published" %}
{% assign hidden_repos = repos | where: "status", "hidden" %}

<div class="archive-page">
  <p class="archive-intro">
    GitHub 레포를 블로그 글로 자동 정리하기 위한 관리 목록.
    각 레포의 Other 체크박스를 켜면 이 브라우저에서 메인/글 목록에서 빠지고 <a href="{{ '/other/' | relative_url }}">Other</a>에서만 보인다.
  </p>

  <div class="repo-preference-panel">
    <div>
      <strong>Browser View</strong>
      <p>선택값은 이 브라우저에 저장된다. PR 생성 버튼을 누르면 GitHub 로그인 후 블로그 설정 변경 PR을 만든다.</p>
    </div>
    <div class="repo-preference-actions">
      <button type="button" class="repo-reset-button" data-repo-preferences-reset>Other 선택 초기화</button>
      <button type="button" class="repo-save-button" data-repo-preferences-pr>PR 생성</button>
    </div>
  </div>
  <p class="repo-pr-status" data-repo-pr-status hidden></p>

  <section class="archive-section">
    <div class="archive-section-header">
      <h2>Featured</h2>
      <span>{{ featured_repos | size }} repos</span>
    </div>
    <div class="repo-list">
      {% for repo in featured_repos %}
        {% include repo-row.html repo=repo %}
      {% endfor %}
    </div>
  </section>

  <section class="archive-section">
    <div class="archive-section-header">
      <h2>Published</h2>
      <span>{{ published_repos | size }} repos</span>
    </div>
    <div class="repo-list">
      {% for repo in published_repos %}
        {% include repo-row.html repo=repo %}
      {% endfor %}
    </div>
  </section>

  <section class="archive-section repo-other-section" data-repo-other-section>
    <div class="archive-section-header">
      <h2>Other</h2>
      <span data-repo-other-count>{{ hidden_repos | size }} repos</span>
    </div>
    <div class="repo-list" data-repo-other-list>
      {% for repo in hidden_repos %}
        {% include repo-row.html repo=repo %}
      {% endfor %}
    </div>
    <p class="repo-empty-message" data-repo-other-empty>Other로 옮긴 레포가 아직 없다.</p>
  </section>
</div>
