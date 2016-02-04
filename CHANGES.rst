Changelog for autopilot
=======================


0.3.1 (unreleased)
------------------

- Nothing changed yet


0.3.0 (2016-02-04)
------------------

- Add `--version` option, which prints out the current version number

- Add release type option to `release` command. Possible values are patch,
  minor and major. The next version numbers are generated based on this option


0.2.2 (2016-02-02)
------------------

- Fix, unused import was raising an exception


0.2.1 (2016-01-31)
------------------

- Remove twine dependency, now we use distlib to upload the packages

- Fix, use package version on sphinx documentation

- Fix, changelog was not properly generated for new releases
