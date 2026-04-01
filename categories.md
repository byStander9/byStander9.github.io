---
layout: page
title: Categories
permalink: /categories/
---

<div class="archive-page">
  <p class="archive-intro">글을 주제별로 모아보는 페이지.</p>

  {% assign categories = site.categories | sort %}
  {% for category in categories %}
    {% assign category_name = category[0] %}
    {% assign posts = category[1] %}
    <section class="archive-section" id="{{ category_name | slugify }}">
      <div class="archive-section-header">
        <h2>#{{ category_name }}</h2>
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
