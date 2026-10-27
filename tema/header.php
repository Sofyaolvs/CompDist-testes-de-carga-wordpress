<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
<meta charset="<?php bloginfo('charset'); ?>">
<meta name="viewport" content="width=device-width, initial-scale=1">
<?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<header class="barra">
  <div class="container">
    <a class="marca" href="<?php echo esc_url(home_url('/')); ?>"><i></i><?php bloginfo('name'); ?></a>
    <nav class="menu"><a href="<?php echo esc_url(home_url('/')); ?>">Início</a><a href="<?php echo esc_url(home_url('/resultados/')); ?>">Resultados</a></nav>
  </div>
</header>
<?php if (is_home() || is_front_page()) : ?>
<section class="hero">
  <div class="container">
    <span class="tag">Sistemas Distribuídos</span>
    <h1>Desempenho e escalabilidade com WordPress, Nginx e Docker</h1>
    <p>Três cenários de conteúdo avaliados com 1, 2 e 3 instâncias sob carga de até mil usuários simultâneos.</p>
  </div>
</section>
<?php endif; ?>
<main class="container wrap">
