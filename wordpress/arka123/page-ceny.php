<?php
/* Цены и условия. */
defined('ABSPATH') || exit;
get_header();
the_post();
?>
<section class="w pghead has-ark" aria-labelledby="pg-h"><div class="pg-card"><figure class="pg-ark hov"><?php arka_mascot('hero'); ?><figcaption><b>Аркадий</b><span>Проектор, звук и Wi-Fi уже в цене. Доплачивать за них не нужно.</span></figcaption></figure><div class="pg-tx">
  <nav class="crumbs" aria-label="Вы здесь"><a href="<?php echo esc_url(home_url('/')); ?>">Главная</a><span aria-hidden="true">/</span><span aria-current="page">Цены</span></nav>
  <h1 class="h-page" id="pg-h"><?php the_title(); ?></h1>
  <?php if (has_excerpt()) : ?><p class="t-body-l"><?php echo esc_html(get_the_excerpt()); ?></p><?php endif; ?>
  </div></div></section>
<section class="w sec first" aria-labelledby="t-h">
  <div class="head"><h2 class="h-sec" id="t-h">Тарифы на будни до 17:00</h2></div>
  <div class="tiers">
    <div class="tier"><h3 class="t-title">Час</h3><span class="p">90 <small>BYN</small></span><span class="t-small">будни до 17:00, минимум 2 часа</span>
      <ul><li><span class="msi">check</span>Проектор, экран, звук</li><li><span class="msi">check</span>Wi-Fi 500 Мбит/с</li></ul></div>
    <div class="tier hi"><h3 class="t-title">Полдня</h3><span class="p">390 <small>BYN</small></span><span class="t-small">5 часов подряд, чаще всего берут</span>
      <ul><li><span class="msi">check</span>Всё из тарифа «Час»</li><li><span class="msi">check</span>Час на монтаж бесплатно</li></ul></div>
    <div class="tier"><h3 class="t-title">День</h3><span class="p">690 <small>BYN</small></span><span class="t-small">с 9:00 до 19:00</span>
      <ul><li><span class="msi">check</span>Монтаж накануне вечером</li><li><span class="msi">check</span>Хранение реквизита 3 дня</li></ul></div>
  </div>
  
</section>
<section class="w sec" aria-labelledby="x-h">
  <div class="head"><h2 class="h-sec" id="x-h">Доплаты и другое время</h2></div>
  <ul class="rows">
    <li><div><b>Вечер и выходные</b><span>после 17:00, суббота и воскресенье</span></div><em>120 BYN/ч</em></li>
    <li><div><b>Шоурум или выставка</b><span>от 1 до 7 дней, монтаж накануне вечером</span></div><em>690 BYN/день</em></li>
    <li><div><b>Офис на месяц</b><span>до 20 рабочих мест, свои ключи</span></div><em>3 900 BYN/мес</em></li>
    <li><div><b>Кофе-брейк</b><span>кофе, чай, вода и выпечка</span></div><em>от 12 BYN/гость</em></li>
    <li><div><b>Продление до 23:00</b><span>для фуршетов и праздников</span></div><em>120 BYN/ч</em></li>
    <li><div><b>Монтаж и демонтаж</b><span>в тарифах «Полдня» и «День» включён</span></div><em>90 BYN/ч</em></li>
  </ul>
</section>
<section class="w sec" aria-labelledby="r-h">
  <div class="head"><h2 class="h-sec" id="r-h">Условия брони</h2></div>
  <div class="rules">
    <div class="rule"><span class="msi">event_available</span><b>Бронь без предоплаты</b><p>Дату держим 24 часа после заявки. Чтобы закрепить её дольше, нужна предоплата 30%, остальное в день мероприятия.</p></div>
    <div class="rule"><span class="msi">swap_horiz</span><b>Перенос и отмена</b><p>Перенос бесплатный, если до мероприятия больше 7 дней. При поздней отмене предоплату можно перенести на другую дату в течение трёх месяцев.</p></div>
    <div class="rule"><span class="msi">payments</span><b>Оплата</b><p>Картой на месте или по счёту для юрлиц. Документы присылаем на <?php echo esc_html(arka_opt('email')); ?>.</p></div>
    <div class="rule"><span class="msi">restaurant</span><b>Свои подрядчики</b><p>Кейтеринг, декор и техника можно привозить свои: есть отдельный вход и грузовой лифт. Если подрядчиков нет, подскажем проверенных.</p></div>
  </div>
</section>
<?php arka_page_content(); ?>
<section class="w sec"><a class="nextp" href="<?php echo esc_url(home_url('/')); ?>#book-s"><span><small>Дальше</small><b>Выбрать дату и время</b></span><span class="msi">arrow_forward</span></a></section>
<?php get_footer();
