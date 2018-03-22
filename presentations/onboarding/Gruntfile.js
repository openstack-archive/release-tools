/* global module:false */
module.exports = function(grunt) {
    var port = grunt.option('port') || 8000;
    var root = grunt.option('root') || '.';

    if (!Array.isArray(root)) root = [root];

    // Project configuration
    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),
        meta: {
            banner:
                '/*!\n' +
                ' * reveal.js <%= pkg.version %> (<%= grunt.template.today("yyyy-mm-dd, HH:MM") %>)\n' +
                ' * http://lab.hakim.se/reveal-js\n' +
                ' * MIT licensed\n' +
                ' *\n' +
                ' * Copyright (C) 2016 Hakim El Hattab, http://hakim.se\n' +
                ' */'
        },

        uglify: {
            options: {
                banner: '<%= meta.banner %>\n'
            },
            build: {
                src: 'js/reveal.js',
                dest: 'js/reveal.min.js'
            }
        },

        sass: {
            core: {
                files: {
                    'css/reveal.css': 'css/reveal.scss',
                }
            },
            themes: {
                files: [
                    {
                        expand: true,
                        cwd: 'css/theme/source',
                        src: ['*.scss'],
                        dest: 'css/theme',
                        ext: '.css'
                    }
                ]
            }
        },

        autoprefixer: {
            dist: {
                src: 'css/reveal.css'
            }
        },

        cssmin: {
            compress: {
                files: {
                    'css/reveal.min.css': [ 'css/reveal.css' ]
                }
            }
        },

        jshint: {
            options: {
                curly: false,
                eqeqeq: true,
                immed: true,
                esnext: true,
                latedef: true,
                newcap: true,
                noarg: true,
                sub: true,
                undef: true,
                eqnull: true,
                browser: true,
                expr: true,
                globals: {
                    head: false,
                    module: false,
                    console: false,
                    unescape: false,
                    define: false,
                    exports: false
                }
            },
            files: [ 'Gruntfile.js', 'js/reveal.js' ]
        },

        connect: {
            server: {
                options: {
                    port: port,
                    base: root,
                    livereload: true,
                    open: true
                }
            },

        },

        zip: {
            '{{cookiecutter.repo_name}}.zip': [
                'index.html',
                'css/**',
                'js/**',
                'lib/**',
                'images/**',
                'img/**',
                'plugin/**',
                '**.graphviz',
                '**.svg',
                '**.md'
            ]
        },

        watch: {
            js: {
                files: [ 'Gruntfile.js', 'js/reveal.js' ],
                tasks: 'js'
            },
            theme: {
                files: [ 'css/theme/source/*.scss', 'css/theme/template/*.scss' ],
                tasks: 'css-themes'
            },
            css: {
                files: [ 'css/reveal.scss' ],
                tasks: 'css-core'
            },
            html: {
                files: root.map(path => path + '/*.html')
            },
            markdown: {
                files: root.map(path => path + '/*.md')
            },
            graphviz: {
                files: [ '*.graphviz' ],
                tasks: 'exec:graphviz',
            },
            options: {
                livereload: true
            }
        },

        retire: {
            js: ['js/reveal.js', 'lib/js/*.js', 'plugin/**/*.js'],
            node: ['.'],
            options: {}
        },

        exec: {
            rsync: './bin/rsync.sh',
            cog: 'cog.py -r index.html',
            graphviz: 'dot -O -Tsvg *.graphviz'
        }

    });

    // Dependencies
    grunt.loadNpmTasks( 'grunt-contrib-qunit' );
    grunt.loadNpmTasks( 'grunt-contrib-jshint' );
    grunt.loadNpmTasks( 'grunt-contrib-cssmin' );
    grunt.loadNpmTasks( 'grunt-contrib-uglify' );
    grunt.loadNpmTasks( 'grunt-contrib-watch' );
    grunt.loadNpmTasks( 'grunt-sass' );
    grunt.loadNpmTasks( 'grunt-contrib-connect' );
    grunt.loadNpmTasks( 'grunt-autoprefixer' );
    grunt.loadNpmTasks( 'grunt-zip' );
    grunt.loadNpmTasks( 'grunt-retire' );

    // Default task
    grunt.registerTask( 'default', [ 'css', 'js' ] );

    // JS task
    grunt.registerTask( 'js', [ 'jshint', 'uglify', 'qunit' ] );

    // Theme CSS
    grunt.registerTask( 'css-themes', [ 'sass:themes' ] );

    // Core framework CSS
    grunt.registerTask( 'css-core', [ 'sass:core', 'autoprefixer', 'cssmin' ] );

    // All CSS
    grunt.registerTask( 'css', [ 'sass', 'autoprefixer', 'cssmin' ] );

    // Package presentation to archive
    grunt.registerTask( 'package', [ 'default', 'zip' ] );

    // Serve presentation locally
    grunt.registerTask( 'serve', [ 'connect', 'watch' ] );

    // Set up grunt-exec
    grunt.loadNpmTasks('grunt-exec');

    // Aliases for the grunt exec commands
    grunt.registerTask('rsync', ['exec:rsync']);
    grunt.registerTask('cog', ['exec:cog']);

};
