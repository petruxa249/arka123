<?php
/* Форматы: берутся из раздела «Форматы» в админке. */
defined('ABSPATH') || exit;
get_header();
the_post();
?>
<section class="w pghead has-ark" aria-labelledby="pg-h"><div class="pg-card"><figure class="pg-ark hov wide"><?php arka_mascot('formats'); ?><figcaption><b>Аркадий</b><span>Микрофон, бокал или камера: под каждый формат зал уже проверен.</span></figcaption></figure><div class="pg-tx">
  <nav class="crumbs" aria-label="Вы здесь"><a href="<?php echo esc_url(home_url('/')); ?>">Главная</a><span aria-hidden="true">/</span><span aria-current="page">Форматы</span></nav>
  <h1 class="h-page" id="pg-h"><?php the_title(); ?></h1>
  <?php if (has_excerpt()) : ?><p class="t-body-l"><?php echo esc_html(get_the_excerpt()); ?></p><?php endif; ?>
  </div></div></section>
<section class="w" style="padding-top:24px"><nav class="fmt-nav" aria-label="Форматы"><?php arka_formats_nav(); ?></nav></section>
<section class="w sec first"><?php arka_formats_full(); ?></section>
<?php arka_page_content(); ?>
<section class="w sec"><a class="nextp" href="<?php echo esc_url(arka_url('ceny')); ?>"><span><small>Дальше</small><b>Цены и условия</b></span><span class="msi">arrow_forward</span></a></section>
<?php get_footer();
