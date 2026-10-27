<?php get_header(); ?>
<h2 class="secao">Cenários de teste</h2>
<div class="grade">
<?php while (have_posts()) : the_post();
  $rotulo = preg_match('/^Cenario\s+(\d+)/i', get_the_title(), $m) ? 'Cenário ' . $m[1] : 'Post'; ?>
  <article class="card">
    <span class="rotulo"><?php echo esc_html($rotulo); ?></span>
    <h2><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2>
    <span class="data"><?php echo get_the_date(); ?></span>
    <a class="mais" href="<?php the_permalink(); ?>">Abrir cenário →</a>
  </article>
<?php endwhile; ?>
</div>
<?php get_footer(); ?>
