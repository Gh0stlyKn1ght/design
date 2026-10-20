# ROS 2 design

This repository is a [Jekyll](http://jekyllrb.com/) website hosted on [Github Pages](http://pages.github.com/) at http://design.ros2.org/.

The repository/website is meant to be a point around which users can collaborate on the ROS 2 design efforts as well as capture those discussions for posterity.

The best place for discussing these topics is [the Next Generation ROS category on the ROS Discourse](https://discourse.ros.org/c/ng-ros).

## Security handbook — October 2026 revision

The four Security articles now contain revised guidance, with original author credits retained and technical revision/additions by [Juan Carlos Nevarez · Gh0stlyKn1ght](https://github.com/Gh0stlyKn1ght).

- [Updated printable handbook](reports/security-handbook/security-handbook.pdf)
- [Revision summary and technology choices](reports/security-handbook/update-summary.pdf)
- [Source and verification notes](reports/security-handbook/README.md)
- [Non-actuating SROS 2 lab](examples/security-lab/README.md)
- [Historical source snapshots](articles/security_history/README.md) and [historical print reader](reports/security-review/security-reference-reader.pdf)

The revision includes an offline-checked policy and editable vector diagram. The recorded isolated ROS run has six passed cases and one inconclusive case. Physical-robot behavior still requires deployment-specific evidence.

## Working Locally

You can run the site locally by running this command in this repository:

```
jekyll serve --watch --baseurl=''
```

And navgiating to your browser to:

[http://localhost:4000/](http://localhost:4000/)


## Working Locally (Docker)

If you don't want to (or can't) install Ruby and other Jekyll dependencies directly on your machine, you can run the server via Docker. Navigate to the directory containing this repository, and start the server via

```
docker run -v $PWD:/srv/jekyll -p 4000:4000 jekyll/jekyll jekyll serve --watch --incremental
```

You can then navigate your browser to:

[http://localhost:4000/](http://localhost:4000/)


## Site setup

This fork is configured for the project-site path `https://gh0stlykn1ght.github.io/design/`. It does not claim upstream's custom domain. The public site uses static links and no inherited GitHub OAuth/token-storage flow or third-party analytics scripts.

Build with `python tools/site/build.py`, which runs strict Jekyll validation and copies the archived sources as unprocessed downloads. GitHub Pages publication, when enabled for this fork, uses the checked-in Actions workflow. A successful local build is separate from a verified deployment.
