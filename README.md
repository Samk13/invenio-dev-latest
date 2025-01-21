# Dev latest-build

## Test install with uv and pnpm

### How to install

```log
steps to use the new invenio-cli with all in:

1.) check that uv and pnpm are installed
2.) create a new my-site directory with the regular content as usual OR go into your current development my-site directory
2.a) deactivate the active environment
3.) create with uv a virtual environment with uv venv --prompt uv-env && source .venv/env/activate
4.) install invenio-cli with uv pip install "git+https://github.com/utnapischtim/invenio-cli@WIP-merged-up-uv-ports-branches"
5.) copy following text into the .invenio file into the cli section
python_packages_manager = uv
javascript_packages_manager = pnpm
assets_builder = rspack

6.) copy following text into the pyproject.toml file. the file should be created beside the invenio.cfg file
[project]
name = "InvenioRDM"
requires-python = ">= 3.12"
dynamic = ["version"]

dependencies = [
  "invenio-app-rdm[opensearch2]~=13.0.0b2.dev0",
  "uwsgi>=2.0",
  "uwsgitop>=0.11",
  "uwsgi-tools>=1.1.1",

  # have better invenio-cli
  "invenio-cli", # enables overrides

  # rspack
  "flask-webpackext",
  "invenio-assets",
]

[tool.setuptools]
py-modules = [] # necessary to make the packages with setup.py usable with uv

[tool.uv]
prerelease = "allow" # necessary only because of the "dev" tags in the invenio packages,
                     # caused by flask>3 and sqlalchemy>2, should be removed afterwards

# overrides packages from "dependencies"
[tool.uv.sources]
invenio-cli = { git = "https://github.com/utnapischtim/invenio-cli", branch = "WIP-merged-up-uv-ports-branches" }
flask-webpackext = { git = "https://github.com/utnapischtim/flask-webpackext", branch = "make-ready-for-rspack" }
invenio-assets = { git = "https://github.com/slint/invenio-assets", branch = "rspack" }
# invenio-cli = { path = "path/to/invenio-cli", editable = true } # would be local example

7.) run time invenio-cli install to install and to see how long it takes
8.) run time invenio-cli install again to see the behavior with hot cache
```

### Notes on the installation process

When installing you should install with uv:
`uv run invenio-cli install`

after running I encountered an error:

```console
 uv run invenio-cli install
 Updated https://github.com/utnapischtim/flask-webpackext (1732f36)
 Updated https://github.com/slint/invenio-assets (008ea61)
 Updated https://github.com/utnapischtim/invenio-cli (45aba6a)
   Built invenio-assets @ git+https://github.com/slint/invenio-assets@008ea6178b9c03
   Built flask-webpackext @ git+https://github.com/utnapischtim/flask-webpackext@173
   Built pycountry==22.3.5
   Built maxminddb-geolite2==2018.703
   Built mkdocs-jupyter==0.12.0
   Built uwsgi==2.0.28
   Built bibtexparser==1.4.3
   Built ftfy==4.4.3
   Built sphinxcontrib-issuetracker==0.11
   Built flask-mail==0.9.1
   Built jsmin==3.0.1
   Built uwsgitop==0.12
   Built flask-principal==0.4.0
   Built infinity==1.5
   Built speaklater==1.3
   Built python-geoip==1.2
Uninstalled 1 package in 1ms
Installed 262 packages in 341ms
Installing python dependencies... Please be patient, this operation might take some time...
Resolved 298 packages in 0.52ms
Uninstalled 2 packages in 1ms
 - markdown-it-py==3.0.0
 - mdurl==0.1.2
Updating instance path...
Instance path already set.
Symlinking 'invenio.cfg'...
Symlinked /home/samk13/INVENIO/issues/latest-build/latest-build/invenio.cfg successfully.Deleted already existing link.
Symlinking 'templates'...
Symlinked /home/samk13/INVENIO/issues/latest-build/latest-build/templates successfully.Deleted already existing link.
Symlinking 'app_data'...
Symlinked /home/samk13/INVENIO/issues/latest-build/latest-build/app_data successfully.Deleted already existing link.
Reload editable packages
Reloaded successfully editable packages.
Updating statics and assets...
[2025-01-20 10:16:31,717] WARNING in factory: APP_ALLOWED_HOSTS is deprecated and has been replaced by TRUSTED_HOSTS.
 WARN  deprecated @babel/plugin-proposal-class-properties@7.18.6: This proposal has been merged to the ECMAScript standard and thus this plugin is no longer maintained. Please use @babel/plugin-transform-class-properties instead.
 WARN  deprecated redux-devtools-extension@2.13.9: Package moved to @redux-devtools/extension.min-lte@2.4.18: 9.44 MB/15.16 MB
Downloading admin-lte@2.4.18: 15.16 MB/15.16 MB, done
Downloading pdfjs-dist@4.10.38: 10.35 MB/10.35 MB, done
Downloading @swc/core-linux-x64-gnu@1.10.8: 16.72 MB/16.72 MB, done
Downloading @swc/core-linux-x64-musl@1.10.8: 20.58 MB/20.58 MB, done
Downloading @rspack/binding-linux-x64-musl@1.1.8: 22.59 MB/22.59 MB, done
Downloading @rspack/binding-linux-x64-gnu@1.1.8: 24.01 MB/24.01 MB, done
Downloading @napi-rs/canvas-linux-x64-musl@0.1.65: 12.51 MB/12.51 MB, done
Downloading @napi-rs/canvas-linux-x64-gnu@0.1.65: 12.12 MB/12.12 MB, done
 WARN  15 deprecated subdependencies found: @babel/plugin-proposal-nullish-coalescing-operator@7.18.6, @babel/plugin-proposal-numeric-separator@7.18.6, @babel/plugin-proposal-optional-chaining@7.21.0, @babel/plugin-proposal-private-methods@7.18.6, @babel/plugin-proposal-private-property-in-object@7.21.11, @humanwhocodes/config-array@0.13.0, @humanwhocodes/object-schema@2.0.3, bootstrap-colorpicker@2.5.3, ckeditor@4.12.1, eslint@8.57.1, glob@7.2.3, inflight@1.0.6, jvectormap@1.2.2, rimraf@2.7.1, rimraf@3.0.2
Packages: +1207
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Progress: resolved 1242, reused 0, downloaded 1207, added 1207, done
node_modules/.pnpm/@swc+core@1.10.8_@swc+helpers@0.5.15/node_modules/@swc/core: Running postinstall script...
node_modules/.pnpm/@parcel+watcher@2.5.0/node_modules/@parcel/watcher: Running inode_modules/.pnpm/@swc+core@1.10.8_@swc+helpers@0.5.15/node_modules/@swc/core: Running postinstall script, done in 105ms

> invenio-assets@2.0.0 postinstall /home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets
> patch-package

patch-package 6.5.1
Applying patches...
semantic-ui-less@2.5.0 ✔

dependencies:
+ @artsy/fresnel 6.2.1 (8.0.1 is available)
+ @ckeditor/ckeditor5-build-classic 16.0.0 (44.1.0 is available)
+ @ckeditor/ckeditor5-react 2.1.0 (9.4.0 is available)
+ @microlink/react-json-view 1.24.0
+ @semantic-ui-react/css-patch 1.1.3
+ @tinymce/tinymce-react 4.3.2 (5.1.1 is available)
+ admin-lte 2.4.18 (4.0.0-beta3 is available)
+ axios 1.7.9
+ flightjs 1.5.2
+ font-awesome 4.5.0 (4.7.0 is available)
+ formik 2.4.6
+ i18next 20.6.1 (24.2.1 is available)
+ i18next-browser-languagedetector 6.1.8 (8.0.2 is available)
+ jquery 3.7.1
+ lodash 4.17.21
+ luxon 1.28.1 (3.5.0 is available)
+ papaparse 5.5.1
+ path 0.12.7
+ pdfjs-dist 4.10.38
+ prismjs 1.29.0
+ prop-types 15.8.1
+ qs 6.14.0
+ query-string 7.1.3 (9.1.1 is available)
+ react 16.14.0 (19.0.0 is available)
+ react-copy-to-clipboard 5.1.0
+ react-dnd 11.1.3 (16.0.1 is available)
+ react-dnd-html5-backend 11.1.3 (16.0.1 is available)
+ react-dom 16.14.0 (19.0.0 is available)
+ react-dropzone 11.7.1 (14.3.5 is available)
+ react-i18next 11.18.6 (15.4.0 is available)
+ react-invenio-forms 4.5.2
+ react-overridable 0.0.3
+ react-redux 7.2.9 (9.2.0 is available)
+ react-router-dom 6.28.2 (7.1.3 is available)
+ react-searchkit 3.0.0
+ redux 4.2.1 (5.0.1 is available)
+ redux-devtools-extension 2.13.9 deprecated
+ redux-thunk 2.4.2 (3.1.0 is available)
+ select2 4.0.13 (4.1.0-rc.0 is available)
+ semantic-ui-css 2.5.0
+ semantic-ui-less 2.5.0
+ semantic-ui-react 2.1.5
+ tinymce 6.8.5 (7.6.0 is available)
+ video.js 8.21.0
+ yup 0.32.11 (1.6.1 is available)

devDependencies:
+ @babel/core 7.26.0
+ @babel/eslint-parser 7.26.5
+ @babel/plugin-proposal-class-properties 7.18.6 deprecated
+ @babel/plugin-transform-runtime 7.25.9
+ @babel/preset-env 7.26.0
+ @babel/preset-react 7.26.3
+ @babel/register 7.25.9
+ @babel/runtime 7.26.0
+ @inveniosoftware/eslint-config-invenio 2.0.1
+ @rspack/cli 1.1.8
+ @rspack/core 1.1.8
+ @rspack/dev-server 1.0.10
+ @swc/core 1.10.8
+ @swc/helpers 0.5.15
+ ajv 8.17.1
+ autoprefixer 10.4.20
+ browserify-zlib 0.2.0
+ chalk 5.4.1
+ clean-webpack-plugin 4.0.0
+ css-loader 6.11.0 (7.1.2 is available)
+ eslint-config-react-app 7.0.1
+ eslint-friendly-formatter 4.0.1
+ eslint-webpack-plugin 2.7.0 (4.2.0 is available)
+ eventsource-polyfill 0.9.6
+ expose-loader 4.1.0 (5.0.0 is available)
+ file-loader 6.2.0
+ function-bind 1.1.2
+ https-browserify 1.0.0
+ less 4.2.2
+ less-loader 11.1.4 (12.2.0 is available)
+ ora 6.3.1 (8.1.1 is available)
+ patch-package 6.5.1 (8.0.0 is available)
+ postcss-flexbugs-fixes 5.0.2
+ postcss-loader 7.3.4 (8.1.1 is available)
+ postcss-preset-env 8.5.1 (10.1.3 is available)
+ postcss-safe-parser 6.0.0 (7.0.1 is available)
+ prettier 2.8.8 (3.4.2 is available)
+ rimraf 4.4.1 (6.0.1 is available)
+ sass 1.83.4
+ sass-loader 16.0.4
+ stream-browserify 3.0.0
+ stream-http 3.2.0
+ style-loader 3.3.4 (4.0.0 is available)
+ swc-loader 0.2.6
+ terser-webpack-plugin 5.3.11
+ url-loader 4.1.1
+ webpack-bundle-analyzer 4.10.2
+ webpack-bundle-tracker 1.8.1 (3.1.1 is available)

Done in 14.1s
Copying project statics and assets...
Symlinking assets...

> invenio-assets@2.0.0 build-rspack /home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets
> NODE_PRESERVE_SYMLINKS=1 NODE_ENV=production rspack --config ./build/rspack.config.js

assets by status 19.6 MiB [cached] 352 assets
orphan modules 4.07 MiB (javascript) 813 bytes (runtime) [orphan] 1338 modules
runtime modules 4.13 KiB 10 modules
cacheable modules 11.6 MiB (javascript) 172 KiB (css/mini-extract)
  modules by path ./node_modules/ 8.99 MiB (javascript) 46.2 KiB (css/mini-extract) 826 modules
  modules by path ./js/ 1.86 MiB 192 modules
  modules by path ./scss/ 416 bytes (javascript) 125 KiB (css/mini-extract) 16 modules
  modules by path ./translations/ 731 KiB
    ./translations/invenio_app_rdm/i18next.js + 34 modules 330 KiB [code generated]
    + 5 modules
  modules by path ./less/invenio_app_rdm/previewer/*.less 52 bytes (javascript) 317 bytes (css/mini-extract)
    ./less/invenio_app_rdm/previewer/iiif_simple.less 52 bytes [built] [code generated]
    css ./node_modules/.pnpm/css-loader@6.11.0_@rspack+core@1.1.8_@swc+helpers@0.5.15__webpack@5.97.1_@swc+core@1.10.8_@swc+helpers@0.5.15__/node_modules/css-loader/dist/cjs.js!./node_modules/.pnpm/less-loader@11.1.4_less@4.2.2_webpack@5.97.1_@swc+core@1.10.8_@swc+helpers@0.5.15__/node_modules/less-loader/dist/cjs.js!./less/invenio_app_rdm/previewer/iiif_simple.less 317 bytes [built] [code generated]
  /home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets/node_modules/moment/locale|sync|/^\.\/.*$/ 160 bytes [built] [code generated]
  ./util.inspect (ignored) 15 bytes [built] [code generated]

WARNING in ./scss/invenio_previewer/prismjs.scss (./scss/invenio_previewer/prismjs.scss!=!./node_modules/.pnpm/css-loader@6.11.0_@rspack+core@1.1.8_@swc+helpers@0.5.15__webpack@5.97.1_@swc+core@1.10.8_@swc+helpers@0.5.15__/node_modules/css-loader/dist/cjs.js!./node_modules/.pnpm/sass-loader@16.0.4_@rspack+core@1.1.8_@swc+helpers@0.5.15__sass@1.83.4_webpack@5.97.1_@swc+co_kjrmusipfdkgnhzjjqy6ehzfza/node_modules/sass-loader/dist/cjs.js!./scss/invenio_previewer/prismjs.scss)
  ⚠ ModuleWarning: Deprecation Warning on line 8, column 8 of file:///home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets/scss/invenio_previewer/prismjs.scss:8:8:
  │ Sass @import rules are deprecated and will be removed in Dart Sass 3.0.0.
  │
  │ More info and automated migrator: https://sass-lang.com/d/import
  │
  │ 8 | @import "~prismjs/themes/prism";
  │
  │
  │ scss/invenio_previewer/prismjs.scss 9:9  root stylesheet
  │  (from: /home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets/node_modules/.pnpm/sass-loader@16.0.4_@rspack+core@1.1.8_@swc+helpers@0.5.15__sass@1.83.4_webpack@5.97.1_@swc+co_kjrmusipfdkgnhzjjqy6ehzfza/node_modules/sass-loader/dist/cjs.js)


WARNING in ./scss/invenio_theme/admin.scss (./scss/invenio_theme/admin.scss!=!./node_modules/.pnpm/css-loader@6.11.0_@rspack+core@1.1.8_@swc+helpers@0.5.15__webpack@5.97.1_@swc+core@1.10.8_@swc+helpers@0.5.15__/node_modules/css-loader/dist/cjs.js!./node_modules/.pnpm/sass-loader@16.0.4_@rspack+core@1.1.8_@swc+helpers@0.5.15__sass@1.83.4_webpack@5.97.1_@swc+co_kjrmusipfdkgnhzjjqy6ehzfza/node_modules/sass-loader/dist/cjs.js!./scss/invenio_theme/admin.scss)
  ⚠ ModuleWarning: Deprecation Warning on line 8, column 8 of file:///home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets/scss/invenio_theme/admin.scss:8:8:
  │ Sass @import rules are deprecated and will be removed in Dart Sass 3.0.0.
  │
  │ More info and automated migrator: https://sass-lang.com/d/import
  │
  │ 8 | @import "~admin-lte/dist/css/AdminLTE";
  │
  │
  │ scss/invenio_theme/admin.scss 9:9  root stylesheet
  │  (from: /home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets/node_modules/.pnpm/sass-loader@16.0.4_@rspack+core@1.1.8_@swc+helpers@0.5.15__sass@1.83.4_webpack@5.97.1_@swc+co_kjrmusipfdkgnhzjjqy6ehzfza/node_modules/sass-loader/dist/cjs.js)


WARNING in ./scss/invenio_theme/admin.scss (./scss/invenio_theme/admin.scss!=!./node_modules/.pnpm/css-loader@6.11.0_@rspack+core@1.1.8_@swc+helpers@0.5.15__webpack@5.97.1_@swc+core@1.10.8_@swc+helpers@0.5.15__/node_modules/css-loader/dist/cjs.js!./node_modules/.pnpm/sass-loader@16.0.4_@rspack+core@1.1.8_@swc+helpers@0.5.15__sass@1.83.4_webpack@5.97.1_@swc+co_kjrmusipfdkgnhzjjqy6ehzfza/node_modules/sass-loader/dist/cjs.js!./scss/invenio_theme/admin.scss)
  ⚠ ModuleWarning: Deprecation Warning on line 9, column 8 of file:///home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets/scss/invenio_theme/admin.scss:9:8:
  │ Sass @import rules are deprecated and will be removed in Dart Sass 3.0.0.
  │
  │ More info and automated migrator: https://sass-lang.com/d/import
  │
  │ 9 | @import "~admin-lte/dist/css/skins/skin-blue";
  │
  │
  │ scss/invenio_theme/admin.scss 10:9  root stylesheet
  │  (from: /home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets/node_modules/.pnpm/sass-loader@16.0.4_@rspack+core@1.1.8_@swc+helpers@0.5.15__sass@1.83.4_webpack@5.97.1_@swc+co_kjrmusipfdkgnhzjjqy6ehzfza/node_modules/sass-loader/dist/cjs.js)


WARNING in ./scss/invenio_theme/admin.scss (./scss/invenio_theme/admin.scss!=!./node_modules/.pnpm/css-loader@6.11.0_@rspack+core@1.1.8_@swc+helpers@0.5.15__webpack@5.97.1_@swc+core@1.10.8_@swc+helpers@0.5.15__/node_modules/css-loader/dist/cjs.js!./node_modules/.pnpm/sass-loader@16.0.4_@rspack+core@1.1.8_@swc+helpers@0.5.15__sass@1.83.4_webpack@5.97.1_@swc+co_kjrmusipfdkgnhzjjqy6ehzfza/node_modules/sass-loader/dist/cjs.js!./scss/invenio_theme/admin.scss)
  ⚠ ModuleWarning: Deprecation Warning on line 10, column 8 of file:///home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets/scss/invenio_theme/admin.scss:10:8:
  │ Sass @import rules are deprecated and will be removed in Dart Sass 3.0.0.
  │
  │ More info and automated migrator: https://sass-lang.com/d/import
  │
  │ 10 | @import "~select2/dist/css/select2";
  │
  │
  │ scss/invenio_theme/admin.scss 11:9  root stylesheet
  │  (from: /home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets/node_modules/.pnpm/sass-loader@16.0.4_@rspack+core@1.1.8_@swc+helpers@0.5.15__sass@1.83.4_webpack@5.97.1_@swc+co_kjrmusipfdkgnhzjjqy6ehzfza/node_modules/sass-loader/dist/cjs.js)


ERROR in ./node_modules/semantic-ui-less/semantic.less
  × Module build failed:
  ╰─▶   × TypeError: Cannot read properties of undefined (reading '__esModule')
        │     at handleExports (/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets/node_modules/.pnpm/@rspack+core@1.1.8_@swc+helpers@0.5.15/node_modules/@rspack/core/dist/cssExtractLoader.js:170:40)
        │     at /home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets/node_modules/.pnpm/@rspack+core@1.1.8_@swc+helpers@0.5.15/node_modules/@rspack/core/dist/cssExtractLoader.js:264:7
        │     at /home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets/node_modules/.pnpm/@rspack+cli@1.1.8_@rspack+core@1.1.8_@swc+helpers@0.5.15__@types+express@4.17.21_webpack@5.97_qhsrwdzffx6b4fb36zy4qm5ygi/node_modules/@rspack/core/dist/index.js:6301:13


 @ ./js/invenio_previewer/previewer_theme.js

ERROR in
  × Module build failed:
  ╰─▶   ×
        │
        │
        │ @import (multiple) '../../theme.config';
        │ ^
        │ Less resolver error:
        │ '../../theme.config' wasn't found. Tried - /home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets/node_modules/semantic-ui-less/theme.config,../../theme.config
        │
        │ Webpack resolver error details:
        │ undefined
        │
        │ Webpack resolver error missing:
        │ undefined
        │
        │
        │       Error in /home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets/node_modules/semantic-ui-less/definitions/modules/transition.less (line 19, column 0)



ERROR in ./js/invenio_app_rdm/deposit/RDMDepositForm.js
  × Cannot find module '@templates/custom_fields' for matched aliased key '@templates'

 @ ./js/invenio_app_rdm/deposit/index.js

ERROR in ./js/invenio_communities/community/new.js
  × Cannot find module '@templates/custom_fields' for matched aliased key '@templates'


ERROR in ./js/invenio_communities/settings/profile/CommunityProfileForm.js
  × Cannot find module '@templates/custom_fields' for matched aliased key '@templates'

 @ ./js/invenio_communities/settings/profile/index.js

ERROR in ./js/invenio_theme/templates.js
  × Cannot find module '@templates' for matched aliased key '@templates'

 @ ./js/invenio_search_ui/util.js
 @ ./js/invenio_search_ui/app.js

Rspack 1.1.8 compiled with 6 errors and 4 warnings in 3.03 s
 ELIFECYCLE  Command failed with exit code 1.
Traceback (most recent call last):
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/bin/invenio-cli", line 10, in <module>
    sys.exit(invenio_cli())
             ^^^^^^^^^^^^^
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/click/core.py", line 1161, in __call__
    return self.main(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/click/core.py", line 1082, in main
    rv = self.invoke(ctx)
         ^^^^^^^^^^^^^^^^
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/click/core.py", line 1697, in invoke
    return _process_result(sub_ctx.command.invoke(sub_ctx))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/click/core.py", line 1675, in invoke
    rv = super().invoke(ctx)
         ^^^^^^^^^^^^^^^^^^^
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/click/core.py", line 1443, in invoke
    return ctx.invoke(self.callback, **ctx.params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/click/core.py", line 788, in invoke
    return __callback(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/click/decorators.py", line 33, in new_func
    return f(get_current_context(), *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/invenio_cli/cli/install.py", line 23, in install
    ctx.invoke(install_all)
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/click/core.py", line 788, in invoke
    return __callback(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/click/decorators.py", line 92, in new_func
    return ctx.invoke(f, obj, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/click/core.py", line 788, in invoke
    return __callback(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/invenio_cli/cli/install.py", line 61, in install_all
    run_steps(steps, on_fail, on_success)
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/invenio_cli/cli/utils.py", line 21, in run_steps
    response = step.execute()
               ^^^^^^^^^^^^^^
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/invenio_cli/commands/steps.py", line 41, in execute
    response = self.func(**self.args)
               ^^^^^^^^^^^^^^^^^^^^^^
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/invenio_cli/commands/local.py", line 157, in update_statics_and_assets
    project.build()
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/pywebpack/helpers.py", line 57, in inner
    raise RuntimeError("Process exited with code {}".format(exit_code))
RuntimeError: Process exited with code 1
```

## attempt 2

- try again with removing the pre-release tag and add

```toml
  # for app-rdm b2.dev0
  "invenio-communities>=18.0.0.dev1",
  "invenio-rdm-records>=17.0.0.dev1",
  "invenio-requests>=6.0.0.dev1",
  "invenio-vocabularies>=7.0.0.dev1",
  "invenio-jobs>=3.0.0.dev1",
  "invenio-users-resources>=7.0.0.dev1",
  ```

remving the venv and installin again

Same error.
looks like it Missing theme.config in semantic-ui-less

- Check the `.invenio.private` file and update it with the correct instance path.
still give me the same error.

## Final try

Remove the path in `.invenio.private`
and run `pnpm store prune`
and try again
Now it works!

```log
uv run invenio-cli install
Uninstalled 2 packages in 1ms
Installed 263 packages in 309ms
Installing python dependencies... Please be patient, this operation might take some time...
Resolved 298 packages in 0.47ms
Uninstalled 2 packages in 1ms
 - markdown-it-py==3.0.0
 - mdurl==0.1.2
Updating instance path...
Instance path updated successfully.
Symlinking 'invenio.cfg'...
Symlinked /home/samk13/INVENIO/issues/latest-build/latest-build/invenio.cfg successfully.
Symlinking 'templates'...
Symlinked /home/samk13/INVENIO/issues/latest-build/latest-build/templates successfully.
Symlinking 'app_data'...
Symlinked /home/samk13/INVENIO/issues/latest-build/latest-build/app_data successfully.
Reload editable packages
Reloaded successfully editable packages.
Updating statics and assets...
[2025-01-21 14:27:40,583] WARNING in factory: APP_ALLOWED_HOSTS is deprecated and has been replaced by TRUSTED_HOSTS.
 WARN  deprecated @babel/plugin-proposal-class-properties@7.18.6: This proposal has been merged to the ECMAScript standard and thus this plugin is no longer maintained. Please use @babel/plugin-transform-class-properties instead.
 WARN  deprecated redux-devtools-extension@2.13.9: Package moved to @redux-devtools/extension.
Downloading @rspack/binding-linux-x64-musl@1.2.0: 24.29 MB/24.29 MB, done
Downloading @rspack/binding-linux-x64-gnu@1.2.0: 24.30 MB/24.30 MB, done
 WARN  15 deprecated subdependencies found: @babel/plugin-proposal-nullish-coalescing-operator@7.18.6, @babel/plugin-proposal-numeric-separator@7.18.6, @babel/plugin-proposal-optional-chaining@7.21.0, @babel/plugin-proposal-private-methods@7.18.6, @babel/plugin-proposal-private-property-in-object@7.21.11, @humanwhocodes/config-array@0.13.0, @humanwhocodes/object-schema@2.0.3, bootstrap-colorpicker@2.5.3, ckeditor@4.12.1, eslint@8.57.1, glob@7.2.3, inflight@1.0.6, jvectormap@1.2.2, rimraf@2.7.1, rimraf@3.0.2
Packages: +1208
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Progress: resolved 1243, reused 1192, downloaded 16, added 1208, done
node_modules/.pnpm/@swc+core@1.10.8_@swc+helpers@0.5.15/node_modules/@swc/core: Running postinstall script, done in 64ms
node_modules/.pnpm/@parcel+watcher@2.5.0/node_modules/@parcel/watcher: Running install script, done in 41ms

> invenio-assets@2.0.0 postinstall /home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets
> patch-package

patch-package 6.5.1
Applying patches...
semantic-ui-less@2.5.0 ✔

dependencies:
+ @artsy/fresnel 6.2.1 (8.0.1 is available)
+ @ckeditor/ckeditor5-build-classic 16.0.0 (44.1.0 is available)
+ @ckeditor/ckeditor5-react 2.1.0 (9.4.0 is available)
+ @microlink/react-json-view 1.24.0
+ @semantic-ui-react/css-patch 1.1.3
+ @tinymce/tinymce-react 4.3.2 (5.1.1 is available)
+ admin-lte 2.4.18 (4.0.0-beta3 is available)
+ axios 1.7.9
+ flightjs 1.5.2
+ font-awesome 4.5.0 (4.7.0 is available)
+ formik 2.4.6
+ i18next 20.6.1 (24.2.1 is available)
+ i18next-browser-languagedetector 6.1.8 (8.0.2 is available)
+ jquery 3.7.1
+ lodash 4.17.21
+ luxon 1.28.1 (3.5.0 is available)
+ papaparse 5.5.1
+ path 0.12.7
+ pdfjs-dist 4.10.38
+ prismjs 1.29.0
+ prop-types 15.8.1
+ qs 6.14.0
+ query-string 7.1.3 (9.1.1 is available)
+ react 16.14.0 (19.0.0 is available)
+ react-copy-to-clipboard 5.1.0
+ react-dnd 11.1.3 (16.0.1 is available)
+ react-dnd-html5-backend 11.1.3 (16.0.1 is available)
+ react-dom 16.14.0 (19.0.0 is available)
+ react-dropzone 11.7.1 (14.3.5 is available)
+ react-i18next 11.18.6 (15.4.0 is available)
+ react-invenio-forms 4.5.2
+ react-overridable 0.0.3
+ react-redux 7.2.9 (9.2.0 is available)
+ react-router-dom 6.28.2 (7.1.3 is available)
+ react-searchkit 3.0.0
+ redux 4.2.1 (5.0.1 is available)
+ redux-devtools-extension 2.13.9 deprecated
+ redux-thunk 2.4.2 (3.1.0 is available)
+ select2 4.0.13 (4.1.0-rc.0 is available)
+ semantic-ui-css 2.5.0
+ semantic-ui-less 2.5.0
+ semantic-ui-react 2.1.5
+ tinymce 6.8.5 (7.6.0 is available)
+ video.js 8.21.0
+ yup 0.32.11 (1.6.1 is available)

devDependencies:
+ @babel/core 7.26.0
+ @babel/eslint-parser 7.26.5
+ @babel/plugin-proposal-class-properties 7.18.6 deprecated
+ @babel/plugin-transform-runtime 7.25.9
+ @babel/preset-env 7.26.0
+ @babel/preset-react 7.26.3
+ @babel/register 7.25.9
+ @babel/runtime 7.26.0
+ @inveniosoftware/eslint-config-invenio 2.0.1
+ @rspack/cli 1.2.0
+ @rspack/core 1.2.0
+ @rspack/dev-server 1.0.10
+ @swc/core 1.10.8
+ @swc/helpers 0.5.15
+ ajv 8.17.1
+ autoprefixer 10.4.20
+ browserify-zlib 0.2.0
+ chalk 5.4.1
+ clean-webpack-plugin 4.0.0
+ css-loader 6.11.0 (7.1.2 is available)
+ eslint-config-react-app 7.0.1
+ eslint-friendly-formatter 4.0.1
+ eslint-webpack-plugin 2.7.0 (4.2.0 is available)
+ eventsource-polyfill 0.9.6
+ expose-loader 4.1.0 (5.0.0 is available)
+ file-loader 6.2.0
+ function-bind 1.1.2
+ https-browserify 1.0.0
+ less 4.2.2
+ less-loader 11.1.4 (12.2.0 is available)
+ ora 6.3.1 (8.1.1 is available)
+ patch-package 6.5.1 (8.0.0 is available)
+ postcss-flexbugs-fixes 5.0.2
+ postcss-loader 7.3.4 (8.1.1 is available)
+ postcss-preset-env 8.5.1 (10.1.3 is available)
+ postcss-safe-parser 6.0.0 (7.0.1 is available)
+ prettier 2.8.8 (3.4.2 is available)
+ rimraf 4.4.1 (6.0.1 is available)
+ sass 1.83.4
+ sass-loader 16.0.4
+ stream-browserify 3.0.0
+ stream-http 3.2.0
+ style-loader 3.3.4 (4.0.0 is available)
+ swc-loader 0.2.6
+ terser-webpack-plugin 5.3.11
+ url-loader 4.1.1
+ webpack-bundle-analyzer 4.10.2
+ webpack-bundle-tracker 1.8.1 (3.1.1 is available)

Done in 9s
Copying project statics and assets...
Symlinking assets...

> invenio-assets@2.0.0 build-rspack /home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets
> NODE_PRESERVE_SYMLINKS=1 NODE_ENV=production rspack --config ./build/rspack.config.js

assets by path ../js/pdfjs/ 13.8 MiB
  assets by path ../js/pdfjs/cmaps/*.bcmap 1.11 MiB 168 assets
  assets by path ../js/pdfjs/web/ 958 KiB 31 assets
  assets by path ../js/pdfjs/build/ 11.8 MiB 9 assets
  asset ../js/pdfjs/cmaps/LICENSE 2.03 KiB [emitted] [from: LICENSE] [copied]
assets by info 16.7 MiB [immutable] 163 assets
assets by path css/*.map 1.07 MiB
  assets by chunk 934 KiB (auxiliary id hint: vendors)
    asset css/1502.1a6bef97696545ac.css.map 886 KiB [emitted] [dev] (auxiliary id hint: vendors)
    asset css/3139.5b05f69b9d191f5b.css.map 48.3 KiB [emitted] [dev] (auxiliary id hint: vendors)
  + 8 assets
assets by path js/skins/ 95.8 KiB
  asset js/skins/ui/oxide/skin.min.css 72.2 KiB [emitted] [from: skin.min.css] [copied]
  asset js/skins/ui/oxide/content.min.css 22.5 KiB [emitted] [from: content.min.css] [copied]
  asset js/skins/content/default/content.css 1.1 KiB [emitted] [from: content.css] [copied]
orphan modules 7.61 MiB (javascript) 6.95 MiB (asset) 1.82 KiB (runtime) [orphan] 1374 modules
runtime modules 3.18 KiB 8 modules
cacheable modules 11.6 MiB (javascript) 1.31 MiB (css/mini-extract)
  modules by path ./node_modules/ 8.99 MiB (javascript) 1.19 MiB (css/mini-extract) 826 modules
  modules by path ./js/ 1.85 MiB 192 modules
  modules by path ./scss/ 416 bytes (javascript) 125 KiB (css/mini-extract) 16 modules
  modules by path ./translations/ 731 KiB 6 modules
  modules by path ./less/invenio_app_rdm/previewer/*.less 52 bytes (javascript) 317 bytes (css/mini-extract)
    ./less/invenio_app_rdm/previewer/iiif_simple.less 52 bytes [built] [code generated]
    css ./node_modules/.pnpm/css-loader@6.11.0_@rspack+core@1.2.0_@swc+helpers@0.5.15__webpack@5.97.1_@swc+core@1.10.8_@swc+helpers@0.5.15__/node_modules/css-loader/dist/cjs.js!./node_modules/.pnpm/less-loader@11.1.4_less@4.2.2_webpack@5.97.1_@swc+core@1.10.8_@swc+helpers@0.5.15__/node_modules/less-loader/dist/cjs.js!./less/invenio_app_rdm/previewer/iiif_simple.less 317 bytes [built] [code generated]
  modules by path /home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets/ 320 bytes
    /home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets/templates/custom_fields|lazy|/^\.\/.*\.js$/|groupOptions: {}|namespace object 160 bytes [built] [code generated]
    /home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets/templates|eager|/^\.\/.*$/|groupOptions: {}|namespace object 160 bytes [built] [code generated]
  /home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets/node_modules/moment/locale|sync|/^\.\/.*$/ 160 bytes [built] [code generated]
  ./util.inspect (ignored) 15 bytes [built] [code generated]

WARNING in ⚠ 'ActiveHover' is not recognized as a valid pseudo-class. Did you mean '::ActiveHover' (pseudo-element) or is this a typo? at css/1502.4e2e0879260385ae.css:17222:27


WARNING in ⚠ 'ActiveHover' is not recognized as a valid pseudo-class. Did you mean '::ActiveHover' (pseudo-element) or is this a typo? at css/1502.4e2e0879260385ae.css:17223:19


WARNING in ⚠ Pseudo-elements like '::before' or '::after' can't be followed by selectors like 'Delim('.')' at css/1502.4e2e0879260385ae.css:43543:36


WARNING in ./scss/invenio_previewer/prismjs.scss (./scss/invenio_previewer/prismjs.scss!=!./node_modules/.pnpm/css-loader@6.11.0_@rspack+core@1.2.0_@swc+helpers@0.5.15__webpack@5.97.1_@swc+core@1.10.8_@swc+helpers@0.5.15__/node_modules/css-loader/dist/cjs.js!./node_modules/.pnpm/sass-loader@16.0.4_@rspack+core@1.2.0_@swc+helpers@0.5.15__sass@1.83.4_webpack@5.97.1_@swc+co_gno76hykkv7xt6hxcfji3qsdje/node_modules/sass-loader/dist/cjs.js!./scss/invenio_previewer/prismjs.scss)
  ⚠ ModuleWarning: Deprecation Warning on line 8, column 8 of file:///home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets/scss/invenio_previewer/prismjs.scss:8:8:
  │ Sass @import rules are deprecated and will be removed in Dart Sass 3.0.0.
  │
  │ More info and automated migrator: https://sass-lang.com/d/import
  │
  │ 8 | @import "~prismjs/themes/prism";
  │
  │
  │ scss/invenio_previewer/prismjs.scss 9:9  root stylesheet
  │  (from: /home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets/node_modules/.pnpm/sass-loader@16.0.4_@rspack+core@1.2.0_@swc+helpers@0.5.15__sass@1.83.4_webpack@5.97.1_@swc+co_gno76hykkv7xt6hxcfji3qsdje/node_modules/sass-loader/dist/cjs.js)


WARNING in ./scss/invenio_theme/admin.scss (./scss/invenio_theme/admin.scss!=!./node_modules/.pnpm/css-loader@6.11.0_@rspack+core@1.2.0_@swc+helpers@0.5.15__webpack@5.97.1_@swc+core@1.10.8_@swc+helpers@0.5.15__/node_modules/css-loader/dist/cjs.js!./node_modules/.pnpm/sass-loader@16.0.4_@rspack+core@1.2.0_@swc+helpers@0.5.15__sass@1.83.4_webpack@5.97.1_@swc+co_gno76hykkv7xt6hxcfji3qsdje/node_modules/sass-loader/dist/cjs.js!./scss/invenio_theme/admin.scss)
  ⚠ ModuleWarning: Deprecation Warning on line 8, column 8 of file:///home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets/scss/invenio_theme/admin.scss:8:8:
  │ Sass @import rules are deprecated and will be removed in Dart Sass 3.0.0.
  │
  │ More info and automated migrator: https://sass-lang.com/d/import
  │
  │ 8 | @import "~admin-lte/dist/css/AdminLTE";
  │
  │
  │ scss/invenio_theme/admin.scss 9:9  root stylesheet
  │  (from: /home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets/node_modules/.pnpm/sass-loader@16.0.4_@rspack+core@1.2.0_@swc+helpers@0.5.15__sass@1.83.4_webpack@5.97.1_@swc+co_gno76hykkv7xt6hxcfji3qsdje/node_modules/sass-loader/dist/cjs.js)


WARNING in ./scss/invenio_theme/admin.scss (./scss/invenio_theme/admin.scss!=!./node_modules/.pnpm/css-loader@6.11.0_@rspack+core@1.2.0_@swc+helpers@0.5.15__webpack@5.97.1_@swc+core@1.10.8_@swc+helpers@0.5.15__/node_modules/css-loader/dist/cjs.js!./node_modules/.pnpm/sass-loader@16.0.4_@rspack+core@1.2.0_@swc+helpers@0.5.15__sass@1.83.4_webpack@5.97.1_@swc+co_gno76hykkv7xt6hxcfji3qsdje/node_modules/sass-loader/dist/cjs.js!./scss/invenio_theme/admin.scss)
  ⚠ ModuleWarning: Deprecation Warning on line 9, column 8 of file:///home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets/scss/invenio_theme/admin.scss:9:8:
  │ Sass @import rules are deprecated and will be removed in Dart Sass 3.0.0.
  │
  │ More info and automated migrator: https://sass-lang.com/d/import
  │
  │ 9 | @import "~admin-lte/dist/css/skins/skin-blue";
  │
  │
  │ scss/invenio_theme/admin.scss 10:9  root stylesheet
  │  (from: /home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets/node_modules/.pnpm/sass-loader@16.0.4_@rspack+core@1.2.0_@swc+helpers@0.5.15__sass@1.83.4_webpack@5.97.1_@swc+co_gno76hykkv7xt6hxcfji3qsdje/node_modules/sass-loader/dist/cjs.js)


WARNING in ./scss/invenio_theme/admin.scss (./scss/invenio_theme/admin.scss!=!./node_modules/.pnpm/css-loader@6.11.0_@rspack+core@1.2.0_@swc+helpers@0.5.15__webpack@5.97.1_@swc+core@1.10.8_@swc+helpers@0.5.15__/node_modules/css-loader/dist/cjs.js!./node_modules/.pnpm/sass-loader@16.0.4_@rspack+core@1.2.0_@swc+helpers@0.5.15__sass@1.83.4_webpack@5.97.1_@swc+co_gno76hykkv7xt6hxcfji3qsdje/node_modules/sass-loader/dist/cjs.js!./scss/invenio_theme/admin.scss)
  ⚠ ModuleWarning: Deprecation Warning on line 10, column 8 of file:///home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets/scss/invenio_theme/admin.scss:10:8:
  │ Sass @import rules are deprecated and will be removed in Dart Sass 3.0.0.
  │
  │ More info and automated migrator: https://sass-lang.com/d/import
  │
  │ 10 | @import "~select2/dist/css/select2";
  │
  │
  │ scss/invenio_theme/admin.scss 11:9  root stylesheet
  │  (from: /home/samk13/INVENIO/issues/latest-build/latest-build/.venv/var/instance/assets/node_modules/.pnpm/sass-loader@16.0.4_@rspack+core@1.2.0_@swc+helpers@0.5.15__sass@1.83.4_webpack@5.97.1_@swc+co_gno76hykkv7xt6hxcfji3qsdje/node_modules/sass-loader/dist/cjs.js)


Rspack 1.2.0 compiled with 7 warnings in 6.17 s
Assets build
Dependencies installed successfully.

```

## Development

When I try to install local packages I got this error:

```log

./install_local_packages.sh
Installing dev packages ...
warning: `VIRTUAL_ENV=/home/samk13/.pyenv/versions/3.12.8/envs/latest-build` does not match the project environment path `.venv` and will be ignored
Installing python dependencies...
Resolved 276 packages in 3.66s
   Built invenio-app-rdm @ file:///home/samk13/INVENIO/issues/invenio-app-rdm
Prepared 57 packages in 1.66s
Uninstalled 56 packages in 333ms
Installed 57 packages in 64ms
 - alembic==1.14.1
 + alembic==1.10.4
 - celery==5.4.0
 + celery==5.3.6
 - flask==3.1.0
 + flask==2.2.5
 - flask-alembic==3.1.1
 + flask-alembic==2.0.1
 + flask-oauthlib==0.9.6
 - flask-sqlalchemy==3.1.1
 + flask-sqlalchemy==2.5.1
 - invenio-access==4.0.0
 + invenio-access==3.0.2
 - invenio-accounts==6.0.0
 + invenio-accounts==5.1.7
 - invenio-administration==3.0.0
 + invenio-administration==2.9.0
 - invenio-app==2.0.0
 + invenio-app==1.5.1
 - invenio-app-rdm==13.0.0b2.dev0
 + invenio-app-rdm==13.0.0b1.dev27 (from file:///home/samk13/INVENIO/issues/invenio-app-rdm)
 - invenio-assets==4.0.0 (from git+https://github.com/slint/invenio-assets@008ea6178b9c03cf7b6483b5b9f3c45848aa4683)
 + invenio-assets==3.1.0
 - invenio-banners==4.0.0
 + invenio-banners==3.2.0
 - invenio-base==2.0.0
 + invenio-base==1.4.0
 - invenio-cache==2.0.0
 + invenio-cache==1.3.1
 - invenio-celery==2.0.0
 + invenio-celery==1.3.2
 - invenio-communities==18.0.0.dev1
 + invenio-communities==17.8.1
 - invenio-db==2.0.0
 + invenio-db==1.3.1
 - invenio-drafts-resources==6.0.0
 + invenio-drafts-resources==5.1.0
 - invenio-files-rest==3.0.0
 + invenio-files-rest==2.2.4
 - invenio-formatter==3.0.0
 + invenio-formatter==2.0.4
 - invenio-github==2.0.0
 + invenio-github==1.5.2
 - invenio-i18n==3.0.0
 + invenio-i18n==2.2.0
 - invenio-indexer==3.0.0
 + invenio-indexer==2.4.0
 - invenio-jobs==3.0.0.dev1
 + invenio-jobs==1.1.1
 - invenio-jsonschemas==2.0.0
 + invenio-jsonschemas==1.1.5
 - invenio-logging==4.0.2
 + invenio-logging==2.1.4
 - invenio-notifications==1.0.0
 + invenio-notifications==0.6.1
 - invenio-oaiserver==3.1.0
 + invenio-oaiserver==2.3.0
 - invenio-oauth2server==3.0.0
 + invenio-oauth2server==2.4.1
 - invenio-oauthclient==5.1.0
 + invenio-oauthclient==4.1.3
 - invenio-pages==5.0.0
 + invenio-pages==4.1.2
 - invenio-pidstore==2.0.0
 + invenio-pidstore==1.3.4
 - invenio-previewer==3.0.0
 + invenio-previewer==2.2.2
 - invenio-rdm-records==17.0.0.dev1
 + invenio-rdm-records==16.7.0
 - invenio-records==3.0.2
 + invenio-records==2.4.1
 - invenio-records-permissions==1.0.0
 + invenio-records-permissions==0.22.0
 - invenio-records-resources==7.0.0
 + invenio-records-resources==6.5.0
 - invenio-records-rest==3.0.0
 + invenio-records-rest==2.4.1
 - invenio-records-ui==2.0.0
 + invenio-records-ui==1.2.2
 - invenio-requests==6.0.0.dev1
 + invenio-requests==5.5.0
 - invenio-rest==2.0.0
 + invenio-rest==1.5.0
 - invenio-search-ui==4.0.0
 + invenio-search-ui==3.0.1
 - invenio-stats==5.0.0
 + invenio-stats==4.3.0
 - invenio-theme==4.0.1
 + invenio-theme==3.6.1
 - invenio-userprofiles==4.0.0
 + invenio-userprofiles==3.0.2
 - invenio-users-resources==7.0.0.dev1
 + invenio-users-resources==6.1.3
 - invenio-vocabularies==7.0.0.dev1
 + invenio-vocabularies==6.11.0
 - itsdangerous==2.2.0
 + itsdangerous==2.0.1
 - oauthlib==3.2.2
 + oauthlib==2.1.0
 - requests-oauthlib==2.0.0
 + requests-oauthlib==1.1.0
 - sqlalchemy==2.0.37
 + sqlalchemy==1.4.54
 - sqlalchemy-continuum==1.4.2
 + sqlalchemy-continuum==1.4.1
 - sqlalchemy-utils==0.41.2
 + sqlalchemy-utils==0.38.3
 - watchdog==6.0.0
 + watchdog==2.2.1
 - werkzeug==3.1.3
 + werkzeug==2.2.3
 - wtforms-alchemy==0.19.0
 + wtforms-alchemy==0.18.0
Packages ('/home/samk13/INVENIO/issues/invenio-app-rdm',) installed successfully.
Rebuilding assets...
Traceback (most recent call last):
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/bin/invenio-cli", line 10, in <module>
    sys.exit(invenio_cli())
             ^^^^^^^^^^^^^
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/click/core.py", line 1161, in __call__
    return self.main(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/click/core.py", line 1082, in main
    rv = self.invoke(ctx)
         ^^^^^^^^^^^^^^^^
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/click/core.py", line 1697, in invoke
    return _process_result(sub_ctx.command.invoke(sub_ctx))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/click/core.py", line 1697, in invoke
    return _process_result(sub_ctx.command.invoke(sub_ctx))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/click/core.py", line 1443, in invoke
    return ctx.invoke(self.callback, **ctx.params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/click/core.py", line 788, in invoke
    return __callback(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/click/decorators.py", line 92, in new_func
    return ctx.invoke(f, obj, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/click/core.py", line 788, in invoke
    return __callback(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/invenio_cli/cli/packages.py", line 72, in install
    AssetsCommands(cli_config).update_statics_and_assets(
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/invenio_cli/commands/local.py", line 130, in update_statics_and_assets
    app = create_ui()
          ^^^^^^^^^^^
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/invenio_base/app.py", line 111, in _create_app
    config_loader(app, **kwargs)
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/invenio_app/factory.py", line 61, in config_loader
    invenio_config_loader(app, **kwargs_config)
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/invenio_config/utils.py", line 55, in _config_loader
    InvenioConfigEntryPointModule(app=app)
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/invenio_config/entrypoint.py", line 35, in __init__
    self.init_app(app)
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/invenio_config/entrypoint.py", line 46, in init_app
    app.config.from_object(ep.load())
                           ^^^^^^^^^
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/pkg_resources/__init__.py", line 2773, in load
    return self.resolve()
           ^^^^^^^^^^^^^^
  File "/home/samk13/INVENIO/issues/latest-build/latest-build/.venv/lib/python3.12/site-packages/pkg_resources/__init__.py", line 2779, in resolve
    module = __import__(self.module_name, fromlist=['__name__'], level=0)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ModuleNotFoundError: No module named 'invenio_app_rdm'
```