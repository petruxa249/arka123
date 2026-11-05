<?php defined('ABSPATH') || exit; ?><!doctype html>
<html <?php language_attributes(); ?>>
<head>
<meta charset="<?php bloginfo('charset'); ?>">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>
<?php if (is_front_page()) : ?><div class="loader" id="loader" role="status" aria-label="Загрузка"><div data-arka-loader></div><div class="count"><span id="arkaCount">0</span> / 123 м²</div></div><?php endif; ?>
<div class="site">

<header class="bar">
  <div class="w">
    <a class="logo" href="<?php echo esc_url(home_url('/')); ?>" aria-label="АРКА 123, на главную"></a>
    <nav class="nav" aria-label="Разделы"><?php foreach (arka_nav_items() as $i => $it) printf('<a%s href="%s"%s>%s</a>', $i >= 3 ? ' class="nx"' : '', esc_url($it['url']), $it['cur'] ? ' aria-current="page"' : '', esc_html($it['title'])); ?></nav>
    <div class="telw"><button class="tel-btn" type="button" id="telBtn" aria-label="Телефон" aria-expanded="false"><span class="msi">call</span></button><div class="tel-pop" id="telPop" hidden><b><?php echo esc_html(arka_opt('phone')); ?></b><span><?php echo esc_html(arka_opt('phone_note')); ?></span></div></div>
    <a class="btn btn-gold" href="<?php echo esc_url(arka_book_url()); ?>">Забронировать</a>
    <button class="burger" type="button" aria-label="Меню" aria-expanded="false" aria-controls="mmenu"><span class="msi">menu</span></button>
  </div>
  <nav class="mmenu" id="mmenu" hidden aria-label="Меню">
    <a href="<?php echo esc_url(home_url('/')); ?>"<?php if (is_front_page()) echo ' aria-current="page"'; ?>>Главная</a>
    <?php foreach (arka_nav_items() as $it) printf('<a href="%s"%s>%s</a>', esc_url($it['url']), $it['cur'] ? ' aria-current="page"' : '', esc_html($it['title'])); ?>
    <a href="<?php echo esc_url(arka_book_url()); ?>">Бронь</a>
    <a class="mtel" href="<?php echo esc_attr(arka_tel()); ?>"><span class="msi">call</span><?php echo esc_html(arka_opt('phone')); ?></a>
  </nav>
</header>

<main>
