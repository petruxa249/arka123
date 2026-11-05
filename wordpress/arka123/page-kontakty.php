<?php
/* Контакты, дорога, реквизиты. */
defined('ABSPATH') || exit;
get_header();
the_post();
?>
<section class="w pghead has-ark" aria-labelledby="pg-h"><div class="pg-card"><figure class="pg-ark hov"><?php arka_mascot('sign'); ?><figcaption><b>Аркадий</b><span>От метро «Восток» 7 минут. Ищите арку с цифрами 123 на втором этаже.</span></figcaption></figure><div class="pg-tx">
  <nav class="crumbs" aria-label="Вы здесь"><a href="<?php echo esc_url(home_url('/')); ?>">Главная</a><span aria-hidden="true">/</span><span aria-current="page">Контакты</span></nav>
  <h1 class="h-page" id="pg-h"><?php the_title(); ?></h1>
  <?php if (has_excerpt()) : ?><p class="t-body-l"><?php echo esc_html(get_the_excerpt()); ?></p><?php endif; ?>
  </div></div></section>
<section class="w sec first" id="contact-s" aria-labelledby="contact-h">
  <div class="contact">
    <div>
      <div class="head"><h2 class="h-sec" id="contact-h">Ответим за 15 минут</h2></div>
      <ul class="list">
        <li><svg class="tg" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M21.4 4.2 2.9 11.3c-1.3.5-1.3 1.2-.2 1.5l4.7 1.5 1.8 5.6c.2.6.1.9.8.9.5 0 .7-.2 1-.5l2.3-2.2 4.8 3.5c.9.5 1.5.2 1.7-.8l3.1-14.7c.3-1.3-.5-1.9-1.5-1.5zM8.6 14.1l9.6-6.1c.5-.3.9-.1.5.2l-8.2 7.4-.3 3.4z"/></svg><div><b>Telegram <?php echo esc_html('@' . arka_opt('telegram')); ?></b><span><?php echo esc_html(arka_opt('manager')); ?>, менеджер, отвечает за 15 минут</span></div></li>
        <li><span class="msi">call</span><div><b><?php echo esc_html(arka_opt('phone')); ?></b><span><?php echo esc_html(arka_opt('phone_note')); ?></span></div></li>
        <li><span class="msi">mail</span><div><b><?php echo esc_html(arka_opt('email')); ?></b><span>Счета и документы для юрлиц</span></div></li>
        <li><span class="msi">directions_subway</span><div><b>Метро «Восток», 7 минут</b><span>Вход со двора, парковка на 30 мест</span></div></li>
      </ul>
      <div class="btns" style="padding-top:20px"><a class="btn btn-filled" href="<?php echo esc_url('https://t.me/' . arka_opt('telegram')); ?>" target="_blank" rel="noopener">Написать в Telegram</a><a class="btn btn-outlined" href="https://yandex.by/maps/?text=%D0%9C%D0%B8%D0%BD%D1%81%D0%BA%2C%20%D1%83%D0%BB.%20%D0%9C%D1%81%D1%82%D0%B8%D1%81%D0%BB%D0%B0%D0%B2%D1%86%D0%B0%2C%2010" target="_blank" rel="noopener"><span class="msi">map</span>Открыть карту</a></div>
    </div>
    <div class="ph"><img src="<?php echo esc_url(arka_asset('ph-ext.jpg')); ?>" alt="Улица у здания с арочными окнами" loading="lazy" width="900" height="507" decoding="async"></div>
  </div>
</section>
<section class="w sec" aria-labelledby="way-h">
  <div class="head"><h2 class="h-sec" id="way-h">Как добраться</h2></div>
  <ol class="route" style="padding:0">
    <li><b>Метро «Восток»</b><span>Выход к Национальной библиотеке, дальше прямо по улице Мстиславца.</span></li>
    <li><b>Угловой дом № 10</b><span>Ищите окно второго этажа в форме арки с цифрами 123.</span></li>
    <li><b>Вход со двора</b><span>Парковка на 30 мест у здания бесплатная. Для подрядчиков отдельный вход и грузовой лифт.</span></li>
  </ol>
</section>
<section class="w sec" aria-labelledby="req-h">
  <div class="head"><h2 class="h-sec" id="req-h">Реквизиты</h2></div>
  <dl class="req">
    <dt>Компания</dt><dd><?php echo esc_html(arka_opt('company')); ?></dd>
    <dt>УНП</dt><dd><?php echo esc_html(arka_opt('unp')); ?></dd>
    <dt>Адрес</dt><dd>220114, Минск, ул. Мстиславца, 10</dd>
    <dt>Почта для документов</dt><dd><?php echo esc_html(arka_opt('email')); ?></dd>
  </dl>
</section><?php arka_page_content(); ?>

<?php get_footer();
