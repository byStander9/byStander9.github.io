---
layout: page
title: Tags
permalink: /tags/
---

<div class="archive-page">
  <p class="archive-intro">세부 키워드별로 글을 모아보는 페이지.</p>

  {% assign tags = site.tags | sort %}
  {% for tag in tags %}
    {% assign tag_name = tag[0] %}
    {% assign posts = tag[1] %}
    <section class="archive-section" id="{{ tag_name | slugify }}">
      <div class="archive-section-header">
        <h2>#{{ tag_name }}</h2>
        <span>{{ posts | size }} posts</span>
      </div>
      <ul class="archive-post-list">
        {% for post in posts %}
          <li>
            <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
            <time>{{ post.date | date: "%Y.%m.%d" }}</time>
          </li>
        {% endfor %}
      </ul>
    </section>
  {% endfor %}
</div>
