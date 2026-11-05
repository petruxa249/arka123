<?php
/* Запасной шаблон: список записей (блог в теме не используется). */
defined('ABSPATH') || exit;
get_header(); ?>
<section class="w pghead"><div class="pg-tx"><?php arka_crumbs(is_404() ? 'Страница не найдена' : wp_get_document_title()); ?><h1 class="h-page"><?php echo is_404() ? 'Такой страницы нет' : esc_html(wp_get_document_title()); ?></h1></div></section>
<section class="w"><div class="prose"><?php if (have_posts() && !is_404()) : while (have_posts()) : the_post(); ?><h2><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2><?php the_excerpt(); endwhile; else : ?><p>Вернитесь <a href="<?php echo esc_url(home_url('/')); ?>">на главную</a>, там бронь и всё о зале.</p><?php endif; ?></div></section>
<?php get_footer();
