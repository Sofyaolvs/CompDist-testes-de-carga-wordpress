<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
<meta charset="<?php bloginfo('charset'); ?>">
<meta name="viewport" content="width=device-width, initial-scale=1">
<?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<header class="topo">
  <h1><a href="<?php echo esc_url(home_url('/')); ?>"><?php bloginfo('name'); ?></a></h1>
  <p>Wordpress + Nginx + Docker · Testes de carga com Locust</p>
  <nav class="nav"><a href="<?php echo esc_url(home_url('/')); ?>">Início</a></nav>
</header>
<main class="wrap">
