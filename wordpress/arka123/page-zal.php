<?php
/* Зал: галерея, характеристики, план, оснащение, 3D. */
defined('ABSPATH') || exit;
get_header();
the_post();
?>
<section class="w pghead has-ark" aria-labelledby="pg-h"><div class="pg-card"><figure class="pg-ark hov"><?php arka_mascot('window'); ?><figcaption><b>Аркадий</b><span>Окна 4 × 3,5 м открываю каждое утро. Свет здесь до самого вечера.</span></figcaption></figure><div class="pg-tx">
  <nav class="crumbs" aria-label="Вы здесь"><a href="<?php echo esc_url(home_url('/')); ?>">Главная</a><span aria-hidden="true">/</span><span aria-current="page">Зал</span></nav>
  <h1 class="h-page" id="pg-h"><?php the_title(); ?></h1>
  <?php if (has_excerpt()) : ?><p class="t-body-l"><?php echo esc_html(get_the_excerpt()); ?></p><?php endif; ?>
  </div></div></section>
<section class="w sec first" aria-label="Фотографии зала">
  <div class="gal"><a href="<?php echo esc_url(arka_asset('interior-clean.jpg')); ?>" data-lb="Зал без мебели"><img src="<?php echo esc_url(arka_asset('interior-clean.jpg')); ?>" alt="Пустой зал с двумя арочными окнами" loading="lazy" width="1672" height="941" decoding="async"><span>Зал без мебели</span></a><a href="<?php echo esc_url(arka_asset('ph-conf.jpg')); ?>" data-lb="Конференция"><img src="<?php echo esc_url(arka_asset('ph-conf.jpg')); ?>" alt="Зал с рядами стульев для конференции" loading="lazy" width="900" height="507" decoding="async"><span>Конференция</span></a><a href="<?php echo esc_url(arka_asset('ph-ext.jpg')); ?>" data-lb="Здание"><img src="<?php echo esc_url(arka_asset('ph-ext.jpg')); ?>" alt="Улица у здания с арочными окнами" loading="lazy" width="900" height="507" decoding="async"><span>Здание</span></a><a href="<?php echo esc_url(arka_asset('ph-shoot2.jpg')); ?>" data-lb="Арка вблизи"><img src="<?php echo esc_url(arka_asset('ph-shoot2.jpg')); ?>" alt="Арочное окно с видом на город" loading="lazy" width="788" height="1400" decoding="async"><span>Арка вблизи</span></a><a href="<?php echo esc_url(arka_asset('ph-shoot.jpg')); ?>" data-lb="Съёмка у окна"><img src="<?php echo esc_url(arka_asset('ph-shoot.jpg')); ?>" alt="Съёмка у арочного окна" loading="lazy" width="507" height="900" decoding="async"><span>Съёмка у окна</span></a><a href="<?php echo esc_url(arka_asset('ph-show.jpg')); ?>" data-lb="Шоурум"><img src="<?php echo esc_url(arka_asset('ph-show.jpg')); ?>" alt="Вешалки с одеждой в шоуруме" loading="lazy" width="507" height="900" decoding="async"><span>Шоурум</span></a><a href="<?php echo esc_url(arka_asset('ph-party.jpg')); ?>" data-lb="Фуршет на закате"><img src="<?php echo esc_url(arka_asset('ph-party.jpg')); ?>" alt="Фуршет на закате у окна" loading="lazy" width="900" height="678" decoding="async"><span>Фуршет на закате</span></a><a href="<?php echo esc_url(arka_asset('ph-office.jpg')); ?>" data-lb="Офис"><img src="<?php echo esc_url(arka_asset('ph-office.jpg')); ?>" alt="Стеклянные перегородки у входа в зал" loading="lazy" width="900" height="507" decoding="async"><span>Офис</span></a><a href="<?php echo esc_url(arka_asset('ph-show2.jpg')); ?>" data-lb="Глубина зала"><img src="<?php echo esc_url(arka_asset('ph-show2.jpg')); ?>" alt="Зал от входа до окон" loading="lazy" width="788" height="1400" decoding="async"><span>Глубина зала</span></a></div>
  <dialog class="lb" id="lb" aria-label="Фото зала"><figure><img alt=""><figcaption></figcaption></figure>
    <button class="lb-btn p" type="button" data-lb-prev aria-label="Предыдущее фото"><span class="msi">chevron_left</span></button>
    <button class="lb-btn n" type="button" data-lb-next aria-label="Следующее фото"><span class="msi">chevron_right</span></button>
    <button class="lb-btn x" type="button" data-lb-close aria-label="Закрыть"><span class="msi">close</span></button></dialog>
</section>
<section class="w sec" aria-labelledby="spec-h">
  <div class="sec-head spec-head"><div class="head"><h2 class="h-sec" id="spec-h">Характеристики зала</h2></div>
  <figure class="tape-ark hov"><?php arka_mascot('tape'); ?></figure></div>
  <dl class="specs">
    <div><dt>123 м²</dt><dd>Свободная планировка, без перегородок</dd></div>
    <div><dt>4 × 3,5 м</dt><dd>Два арочных окна, подоконник 0,9 м</dd></div>
    <div><dt>4,5 м</dt><dd>Потолки, подвесы для света и декора</dd></div>
    <div><dt>до 100</dt><dd>Гостей театром, 40 за столами</dd></div>
    <div><dt>2 этаж</dt><dd>Вход со двора, грузовой лифт</dd></div>
    <div><dt>500 Мбит/с</dt><dd>Wi-Fi и кабель для трансляций</dd></div>
  </dl>
</section>
<section class="w sec" aria-labelledby="plan-h">
  <div class="head"><h2 class="h-sec" id="plan-h">План и расстановка</h2></div>
  <div class="plan-wrap">
    <figure class="plan" style="margin:0"><svg viewBox="0 0 648 444" role="img" aria-label="План зала: 14,2 на 8,7 метра, два арочных окна по 4 метра в длинной стене, вход с противоположной стороны">
  <rect x="40" y="40" width="568.0" height="348.0" fill="#FBF9F5" stroke="#213641" stroke-width="6"/>
  <g fill="#FDFCFA" stroke="#213641" stroke-width="2">
    <rect x="120.0" y="34" width="160" height="12"/><rect x="368.0" y="34" width="160" height="12"/></g>
  <g fill="#C9A26A" opacity=".16"><path d="M120.0 46 h160 l40 104.0 h-240z"/><path d="M368.0 46 h160 l40 104.0 h-240z"/></g>
  <g font-family="Inter,system-ui,sans-serif" font-size="15" fill="#4D565C" text-anchor="middle">
    <text x="200.0" y="24">окно 4 × 3,5 м</text><text x="448.0" y="24">окно 4 × 3,5 м</text>
    <text x="324.0" y="428.0">14,2 м</text>
    <text x="20" y="214.0" transform="rotate(-90 20 214.0)">8,7 м</text>
    <text x="324.0" y="220.0" font-size="22" fill="#213641">123 м²</text>
    <text x="88.0" y="374.0" font-size="13">экран</text>
    <text x="544.0" y="348.0" font-size="13">гардероб</text>
  </g>
  <rect x="48.0" y="160.0" width="8" height="112.0" fill="#213641"/>
  <rect x="496.0" y="354.0" width="96.0" height="10" rx="2" fill="#DCE7EE"/>
  <g stroke="#213641" stroke-width="2" fill="none"><path d="M424.0 388.0 a44.0 44.0 0 0 1 44.0 -44.0"/></g>
  <rect x="424.0" y="385.0" width="44.0" height="6" fill="#FBF9F5"/>
  <text x="446.0" y="410.0" font-family="Inter,system-ui,sans-serif" font-size="13" fill="#4D565C" text-anchor="middle">вход</text>
</svg><figcaption class="t-small">Схема, размеры по обмеру: 14,2 × 8,7 м.</figcaption></figure>
    <ul class="seat">
      <li><svg viewBox="0 0 48 36" fill="currentColor" aria-hidden="true"><rect x="10" y="2" width="28" height="3" rx="1"/><circle cx="6" cy="13" r="2"/><circle cx="12" cy="13" r="2"/><circle cx="18" cy="13" r="2"/><circle cx="24" cy="13" r="2"/><circle cx="30" cy="13" r="2"/><circle cx="36" cy="13" r="2"/><circle cx="42" cy="13" r="2"/><circle cx="6" cy="20" r="2"/><circle cx="12" cy="20" r="2"/><circle cx="18" cy="20" r="2"/><circle cx="24" cy="20" r="2"/><circle cx="30" cy="20" r="2"/><circle cx="36" cy="20" r="2"/><circle cx="42" cy="20" r="2"/><circle cx="6" cy="27" r="2"/><circle cx="12" cy="27" r="2"/><circle cx="18" cy="27" r="2"/><circle cx="24" cy="27" r="2"/><circle cx="30" cy="27" r="2"/><circle cx="36" cy="27" r="2"/><circle cx="42" cy="27" r="2"/></svg><div><b>Театр</b><span>Лекции, презентации</span></div><em>100</em></li>
      <li><svg viewBox="0 0 48 36" fill="currentColor" aria-hidden="true"><rect x="10" y="2" width="28" height="3" rx="1"/><rect x="4" y="11" width="11" height="3" rx="1"/><circle cx="7" cy="18" r="1.6"/><circle cx="12" cy="18" r="1.6"/><rect x="19" y="11" width="11" height="3" rx="1"/><circle cx="22" cy="18" r="1.6"/><circle cx="27" cy="18" r="1.6"/><rect x="34" y="11" width="11" height="3" rx="1"/><circle cx="37" cy="18" r="1.6"/><circle cx="42" cy="18" r="1.6"/><rect x="4" y="21" width="11" height="3" rx="1"/><circle cx="7" cy="28" r="1.6"/><circle cx="12" cy="28" r="1.6"/><rect x="19" y="21" width="11" height="3" rx="1"/><circle cx="22" cy="28" r="1.6"/><circle cx="27" cy="28" r="1.6"/><rect x="34" y="21" width="11" height="3" rx="1"/><circle cx="37" cy="28" r="1.6"/><circle cx="42" cy="28" r="1.6"/></svg><div><b>Класс</b><span>Мастер-классы, тренинги</span></div><em>40</em></li>
      <li><svg viewBox="0 0 48 36" fill="currentColor" aria-hidden="true"><circle cx="10" cy="10" r="5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="26" cy="8" r="5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="40" cy="14" r="5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="16" cy="26" r="5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="34" cy="28" r="5" fill="none" stroke="currentColor" stroke-width="2"/></svg><div><b>Фуршет</b><span>Праздники, нетворкинг</span></div><em>70</em></li>
      <li><svg viewBox="0 0 48 36" fill="currentColor" aria-hidden="true"><rect x="3" y="4" width="12" height="7" rx="1"/><circle cx="9" cy="15" r="1.8"/><rect x="19" y="4" width="12" height="7" rx="1"/><circle cx="25" cy="15" r="1.8"/><rect x="35" y="4" width="12" height="7" rx="1"/><circle cx="41" cy="15" r="1.8"/><rect x="3" y="20" width="12" height="7" rx="1"/><circle cx="9" cy="31" r="1.8"/><rect x="19" y="20" width="12" height="7" rx="1"/><circle cx="25" cy="31" r="1.8"/><rect x="35" y="20" width="12" height="7" rx="1"/><circle cx="41" cy="31" r="1.8"/></svg><div><b>Офис</b><span>Рабочие места на месяц</span></div><em>20</em></li>
    </ul>
  </div>
</section>
<section class="w sec" aria-labelledby="eq-h">
  <div class="head"><h2 class="h-sec" id="eq-h">Что входит в цену</h2></div>
  <ul class="checks">
    <li><span class="msi">co_present</span><b>Проектор и экран</b><span>Full HD, HDMI и USB-C у кафедры</span></li>
    <li><span class="msi">mic</span><b>Звук</b><span>Колонки и два радиомикрофона</span></li>
    <li><span class="msi">wifi</span><b>Wi-Fi 500 Мбит/с</b><span>Отдельная сеть для трансляций</span></li>
    <li><span class="msi">chair</span><b>100 стульев, 20 столов</b><span>Расставим до вашего прихода</span></li>
    <li><span class="msi">checkroom</span><b>Гардероб</b><span>Вешалки на 100 мест у входа</span></li>
    <li><span class="msi">elevator</span><b>Грузовой лифт</b><span>Отдельный вход для подрядчиков</span></li>
  </ul>
</section>
<section class="w sec" aria-labelledby="tour-h">
  <div class="split rev">
    <div class="split-ph"><img src="<?php echo esc_url(arka_asset('flight-last.jpg')); ?>" alt="Вид внутри зала в конце пролёта через окно" loading="lazy" width="1280" height="720" decoding="async"></div>
    <div class="split-tx">
      <h2 class="h-sec" id="tour-h">Зал в 3D</h2>
      <p class="t-body-l">Пройдитесь по залу и выберите, где поставить сцену. Вживую тоже можно: приезжайте на 15 минут в любой будний день.</p>
      <div class="btns"><a class="btn btn-filled" href="<?php echo esc_url(arka_asset('3d.html')); ?>"><span class="msi">view_in_ar</span>Открыть 3D-режим</a><a class="btn btn-outlined" href="<?php echo esc_url(arka_url('kontakty')); ?>">Как добраться</a></div>
    </div>
  </div>
</section>
<?php arka_page_content(); ?>
<section class="w sec"><a class="nextp" href="<?php echo esc_url(arka_url('formaty')); ?>"><span><small>Дальше</small><b>Форматы мероприятий</b></span><span class="msi">arrow_forward</span></a></section>
<?php get_footer();
