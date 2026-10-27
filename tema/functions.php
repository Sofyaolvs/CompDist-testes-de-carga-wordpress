<?php
add_action('after_setup_theme', function () {
    add_theme_support('title-tag');
    add_theme_support('post-thumbnails');
});

// Lista os cenários na ordem 1, 2, 3 na página inicial.
add_action('pre_get_posts', function ($q) {
    if ($q->is_main_query() && $q->is_home()) {
        $q->set('orderby', 'title');
        $q->set('order', 'ASC');
    }
});

// Carrega o style.css do tema (sem isso a página sai sem estilo).
add_action('wp_enqueue_scripts', function () {
    wp_enqueue_style('sd-moderno', get_stylesheet_uri(), [], '2.1');
});
