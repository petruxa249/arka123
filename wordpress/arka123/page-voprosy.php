<?php
/* Вопросы: берутся из раздела «Вопросы» в админке. */
defined('ABSPATH') || exit;
get_header();
the_post();
?>
<section class="w sec first" id="faq-s" aria-labelledby="faq-h">
  <div class="faq">
    <div class="faq-side">
      <nav class="crumbs" aria-label="Вы здесь"><a href="<?php echo esc_url(home_url('/')); ?>">Главная</a><span aria-hidden="true">/</span><span aria-current="page">Вопросы</span></nav>
      <h1 class="h-page" id="faq-h"><?php the_title(); ?></h1>
      <div class="faq-ark hov"><?php arka_mascot('lost'); ?><p><b>Аркадий, управляющий</b><span>Не нашли ответ? Спросите Анну в Telegram, она отвечает с 9:00 до 21:00. А я пока подержу дверь.</span></p></div>
    </div>
    <div>
      <?php arka_faq_list(-1); ?>

    </div>
  </div>
</section>
<?php arka_page_content(); ?>
<section class="w sec"><a class="nextp" href="<?php echo esc_url(home_url('/')); ?>#book-s"><span><small>Дальше</small><b>Выбрать дату и время</b></span><span class="msi">arrow_forward</span></a></section>
<?php get_footer();
