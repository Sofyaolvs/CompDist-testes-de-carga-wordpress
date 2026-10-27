<?php get_header(); while (have_posts()) : the_post(); ?>
<div class="migalha"><a href="<?php echo esc_url(home_url('/')); ?>">Início</a> / <?php the_title(); ?></div>
<article class="post pagina">
  <h1><?php the_title(); ?></h1>
  <?php the_content(); ?>
</article>
<?php endwhile; get_footer(); ?>
