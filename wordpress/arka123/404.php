<?php defined('ABSPATH') || exit; get_header(); ?>
<section class="w pghead has-ark"><div class="pg-tx"><?php arka_crumbs('Страница не найдена'); ?><h1 class="h-page">Такой страницы нет</h1><p class="t-body-l">Возможно, ссылка устарела. На главной есть бронь и всё о зале.</p><div class="btns"><a class="btn btn-filled" href="<?php echo esc_url(home_url('/')); ?>">На главную</a></div></div>
<figure class="pg-ark hov"><?php arka_mascot('lost'); ?><figcaption><b>Аркадий</b><span>Кажется, мы оба заблудились. Арка на главной.</span></figcaption></figure></section>
<?php get_footer();
