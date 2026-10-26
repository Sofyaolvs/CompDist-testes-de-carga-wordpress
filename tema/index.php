<?php get_header(); ?>
<div class="grade">
<?php while (have_posts()) : the_post(); ?>
  <article class="card">
    <span class="data"><?php echo get_the_date(); ?></span>
    <h2><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2>
    <a class="mais" href="<?php the_permalink(); ?>">Ler post →</a>
  </article>
<?php endwhile; ?>
</div>
<?php get_footer(); ?>
