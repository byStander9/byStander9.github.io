---
layout: page
title: Other
permalink: /other/
---

{% assign repos = site.data.repositories_generated %}

<div class="archive-page">
  <p class="archive-intro">
    Repositories 페이지에서 Other로 옮긴 레포만 모아보는 개인 브라우저용 목록.
    선택값은 이 브라우저의 localStorage에 저장된다.
  </p>

  <section class="archive-section">
    <div class="archive-section-header">
      <h2>Other</h2>
      <span data-repo-other-only-count>0 repos</span>
    </div>
    <div class="repo-list" data-repo-other-only-list>
      {% for repo in repos %}
        {% include repo-row.html repo=repo %}
      {% endfor %}
    </div>
    <p class="repo-empty-message" data-repo-other-only-empty>Other로 옮긴 레포가 아직 없다.</p>
  </section>
</div>
