<?php
/* Обычная страница: заголовок, отрывок, Аркадий и текст из редактора (так устроена «Политика обработки данных»). */
defined('ABSPATH') || exit;
get_header();
the_post();
?>
<section class="w pghead has-ark" aria-labelledby="pg-h"><div class="pg-card"><figure class="pg-ark hov wide"><?php arka_mascot('sheet'); ?><figcaption><b>Аркадий</b><span>Ваши контакты нужны только для ответа на заявку.</span></figcaption></figure><div class="pg-tx">
  <nav class="crumbs" aria-label="Вы здесь"><a href="<?php echo esc_url(home_url('/')); ?>">Главная</a><span aria-hidden="true">/</span><span aria-current="page"><?php the_title(); ?></span></nav>
  <h1 class="h-page" id="pg-h"><?php the_title(); ?></h1>
  <?php if (has_excerpt()) : ?><p class="t-body-l"><?php echo esc_html(get_the_excerpt()); ?></p><?php endif; ?>
  </div></div></section>
<section class="w"><div class="prose"><?php the_content(); ?></div></section>
<?php get_footer();
