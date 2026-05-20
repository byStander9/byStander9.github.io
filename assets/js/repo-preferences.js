(function () {
  "use strict";

  var storageKey = "bystander.repo.other.v1";
  var pendingPrKey = "bystander.repo.pendingPr.v1";

  function readOtherRepos() {
    return readRepoList(storageKey);
  }

  function readRepoList(key) {
    try {
      var value = window.localStorage.getItem(key);
      return value ? JSON.parse(value) : [];
    } catch (_error) {
      return [];
    }
  }

  function writeOtherRepos(repos) {
    window.localStorage.setItem(storageKey, JSON.stringify(repos.sort()));
  }

  function hasRepo(repos, repo) {
    return repos.indexOf(repo) !== -1;
  }

  function setRepo(repos, repo, enabled) {
    var next = repos.filter(function (item) {
      return item !== repo;
    });
    if (enabled) {
      next.push(repo);
    }
    writeOtherRepos(next);
    return next;
  }

  function isOtherRepo(row, otherRepos) {
    var repo = row.getAttribute("data-repo");
    return hasRepo(otherRepos, repo) || row.dataset.defaultStatus === "hidden";
  }

  function hideMainContent(otherRepos) {
    document.querySelectorAll("[data-blog-post][data-repo], [data-home-repo][data-repo]").forEach(function (element) {
      var repo = element.getAttribute("data-repo");
      element.hidden = hasRepo(otherRepos, repo);
    });
  }

  function setupRepositoryPage(otherRepos) {
    var otherList = document.querySelector("[data-repo-other-list]");
    if (!otherList) {
      return;
    }

    var rows = Array.prototype.slice.call(document.querySelectorAll("[data-repo-row][data-repo]"));
    rows.forEach(function (row) {
      var repo = row.getAttribute("data-repo");
      row.dataset.originalParentId = row.parentElement.dataset.repoListId || "";
      if (!row.parentElement.dataset.repoListId) {
        row.parentElement.dataset.repoListId = "repo-list-" + Math.random().toString(36).slice(2);
      }
      row.dataset.originalParentId = row.parentElement.dataset.repoListId;
      row.dataset.originalIndex = Array.prototype.indexOf.call(row.parentElement.children, row).toString();
      var checkbox = row.querySelector("[data-repo-other-toggle]");
      if (checkbox) {
        checkbox.checked = hasRepo(otherRepos, repo);
        checkbox.addEventListener("change", function () {
          otherRepos = setRepo(otherRepos, repo, checkbox.checked);
          applyPreferences(otherRepos);
        });
      }
    });

    var reset = document.querySelector("[data-repo-preferences-reset]");
    if (reset) {
      reset.addEventListener("click", function () {
        writeOtherRepos([]);
        applyPreferences([]);
      });
    }

    var prButton = document.querySelector("[data-repo-preferences-pr]");
    if (prButton) {
      prButton.addEventListener("click", function () {
        createPreferencePullRequest();
      });
    }
  }

  function moveRows(otherRepos) {
    var otherList = document.querySelector("[data-repo-other-list]");
    if (!otherList) {
      return;
    }

    document.querySelectorAll("[data-repo-row][data-repo]").forEach(function (row) {
      var repo = row.getAttribute("data-repo");
      var checkbox = row.querySelector("[data-repo-other-toggle]");
      var shouldMove = isOtherRepo(row, otherRepos);
      if (checkbox) {
        checkbox.checked = shouldMove;
      }

      if (shouldMove && row.parentElement !== otherList) {
        otherList.appendChild(row);
      }

      if (!shouldMove && row.parentElement === otherList) {
        var originalParent = document.querySelector('[data-repo-list-id="' + row.dataset.originalParentId + '"]');
        if (originalParent) {
          originalParent.appendChild(row);
          sortRows(originalParent);
        }
      }
    });

    sortRows(otherList);
    updateOtherCount(otherList);
  }

  function sortRows(list) {
    Array.prototype.slice.call(list.querySelectorAll("[data-repo-row]"))
      .sort(function (a, b) {
        return Number(a.dataset.originalIndex || 0) - Number(b.dataset.originalIndex || 0);
      })
      .forEach(function (row) {
        list.appendChild(row);
      });
  }

  function updateOtherCount(otherList) {
    var count = otherList.querySelectorAll("[data-repo-row]").length;
    var countElement = document.querySelector("[data-repo-other-count]");
    var emptyElement = document.querySelector("[data-repo-other-empty]");
    if (countElement) {
      countElement.textContent = count + " repos";
    }
    if (emptyElement) {
      emptyElement.hidden = count > 0;
    }
  }

  function applyPreferences(otherRepos) {
    hideMainContent(otherRepos);
    moveRows(otherRepos);
    updateOtherOnlyPage(otherRepos);
  }

  function updateOtherOnlyPage(otherRepos) {
    var list = document.querySelector("[data-repo-other-only-list]");
    if (!list) {
      return;
    }

    var count = 0;
    list.querySelectorAll("[data-repo-row][data-repo]").forEach(function (row) {
      var repo = row.getAttribute("data-repo");
      var isOther = isOtherRepo(row, otherRepos);
      row.hidden = !isOther;
      count += isOther ? 1 : 0;
      var checkbox = row.querySelector("[data-repo-other-toggle]");
      if (checkbox) {
        checkbox.checked = isOther;
        checkbox.addEventListener("change", function () {
          var next = setRepo(readOtherRepos(), repo, checkbox.checked);
          applyPreferences(next);
        }, { once: true });
      }
    });

    var countElement = document.querySelector("[data-repo-other-only-count]");
    var emptyElement = document.querySelector("[data-repo-other-only-empty]");
    if (countElement) {
      countElement.textContent = count + " repos";
    }
    if (emptyElement) {
      emptyElement.hidden = count > 0;
    }
  }

  function workerUrl() {
    var meta = document.querySelector('meta[name="repo-pr-worker-url"]');
    return meta ? meta.getAttribute("content").replace(/\/$/, "") : "";
  }

  function selectedOtherRepos() {
    var checked = Array.prototype.slice.call(document.querySelectorAll("[data-repo-other-toggle]:checked"));
    if (checked.length) {
      return checked.map(function (input) {
        return input.value;
      }).sort();
    }
    return readOtherRepos();
  }

  function setStatus(message, isError) {
    var status = document.querySelector("[data-repo-pr-status]");
    if (!status) {
      return;
    }
    status.hidden = false;
    status.textContent = message;
    status.dataset.state = isError ? "error" : "ok";
  }

  function createPreferencePullRequest() {
    var api = workerUrl();
    if (!api) {
      setStatus("_config.yml의 repo_pr_worker_url 설정이 필요하다.", true);
      return;
    }

    var hiddenRepos = selectedOtherRepos();
    window.localStorage.setItem(pendingPrKey, JSON.stringify(hiddenRepos));
    setStatus("GitHub PR 생성을 준비하는 중...", false);

    fetch(api + "/api/preferences/pr", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        hidden_repositories: hiddenRepos,
        return_url: window.location.href.split("#")[0].split("?")[0],
      }),
    })
      .then(function (response) {
        return response.json().then(function (payload) {
          return { response: response, payload: payload };
        });
      })
      .then(function (result) {
        if (result.response.status === 401 && result.payload.login_url) {
          window.location.href = result.payload.login_url;
          return;
        }
        if (!result.response.ok) {
          throw new Error(result.payload.message || result.payload.error || "PR 생성 실패");
        }
        window.localStorage.removeItem(pendingPrKey);
        setStatus("PR이 생성됐다: " + result.payload.pull_request_url, false);
      })
      .catch(function (error) {
        setStatus(error.message, true);
      });
  }

  function resumePendingPr() {
    var params = new URLSearchParams(window.location.search);
    if (params.get("repo_pr_ready") !== "1") {
      return;
    }
    var pending = window.localStorage.getItem(pendingPrKey);
    if (!pending) {
      return;
    }
    try {
      writeOtherRepos(JSON.parse(pending));
      applyPreferences(readOtherRepos());
      createPreferencePullRequest();
    } catch (_error) {
      window.localStorage.removeItem(pendingPrKey);
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    var otherRepos = readOtherRepos();
    setupRepositoryPage(otherRepos);
    applyPreferences(otherRepos);
    resumePendingPr();
  });
})();
