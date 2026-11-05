<?php
/* Записи, которые менеджер правит в админке: «Форматы» (страница форматов) и «Вопросы» (FAQ на главной и на странице вопросов). */
defined('ABSPATH') || exit;

add_action('init', function () {
	register_post_type('arka_format', [
		'labels' => ['name' => 'Форматы', 'singular_name' => 'Формат', 'add_new' => 'Добавить формат', 'add_new_item' => 'Новый формат', 'edit_item' => 'Изменить формат', 'all_items' => 'Все форматы'],
		'public' => false, 'show_ui' => true, 'show_in_rest' => true, 'menu_icon' => 'dashicons-format-gallery', 'menu_position' => 21,
		'supports' => ['title', 'editor', 'thumbnail', 'page-attributes'],
	]);
	register_post_type('arka_faq', [
		'labels' => ['name' => 'Вопросы', 'singular_name' => 'Вопрос', 'add_new' => 'Добавить вопрос', 'add_new_item' => 'Новый вопрос', 'edit_item' => 'Изменить вопрос', 'all_items' => 'Все вопросы'],
		'public' => false, 'show_ui' => true, 'show_in_rest' => true, 'menu_icon' => 'dashicons-editor-help', 'menu_position' => 22,
		'supports' => ['title', 'editor', 'page-attributes'],
	]);
});

/* поля формата */
function arka_format_fields() {
	return [
		'_arka_price'   => ['Цена', 'например 90 или 3 900'],
		'_arka_unit'    => ['Единица', 'BYN/ч, BYN/день, BYN/мес'],
		'_arka_from'    => ['Писать «от» перед ценой', '1 или пусто'],
		'_arka_note'    => ['Подпись к цене', 'будни до 17:00'],
		'_arka_bullets' => ['Пункты списка', 'каждый с новой строки'],
		'_arka_key'     => ['Формат в заявке', 'Конференция, Съёмка, Шоурум или pop-up, Офис на месяц, Фуршет или праздник'],
		'_arka_cta'     => ['Текст кнопки', 'Забронировать'],
		'_arka_img'     => ['Фото из темы', 'если не задана миниатюра: ph-conf.jpg и т. п.'],
		'_arka_alt'     => ['Описание фото', 'для незрячих и поисковиков'],
	];
}

add_action('add_meta_boxes_arka_format', function () {
	add_meta_box('arka-format', 'Цена, пункты и кнопка', function ($post) {
		wp_nonce_field('arka_format', 'arka_format_nonce');
		echo '<table class="form-table">';
		foreach (arka_format_fields() as $k => [$label, $hint]) {
			$v = get_post_meta($post->ID, $k, true);
			echo '<tr><th><label for="' . esc_attr($k) . '">' . esc_html($label) . '</label></th><td>';
			if ($k === '_arka_bullets') echo '<textarea class="large-text" rows="4" id="' . esc_attr($k) . '" name="' . esc_attr($k) . '">' . esc_textarea($v) . '</textarea>';
			else echo '<input class="regular-text" id="' . esc_attr($k) . '" name="' . esc_attr($k) . '" value="' . esc_attr($v) . '">';
			echo '<p class="description">' . esc_html($hint) . '</p></td></tr>';
		}
		echo '</table>';
	}, 'arka_format', 'normal', 'high');
});

add_action('save_post_arka_format', function ($id) {
	if (!isset($_POST['arka_format_nonce']) || !wp_verify_nonce($_POST['arka_format_nonce'], 'arka_format')) return;
	if (!current_user_can('edit_post', $id) || wp_is_post_autosave($id)) return;
	foreach (array_keys(arka_format_fields()) as $k) {
		if (!isset($_POST[$k])) continue;
		$v = wp_unslash($_POST[$k]);
		update_post_meta($id, $k, $k === '_arka_bullets' ? sanitize_textarea_field($v) : sanitize_text_field($v));
	}
});

/* списки в админке: цена и порядок */
add_filter('manage_arka_format_posts_columns', fn($c) => array_slice($c, 0, 2) + ['price' => 'Цена', 'order' => 'Порядок'] + $c);
add_action('manage_arka_format_posts_custom_column', function ($col, $id) {
	if ($col === 'price') echo esc_html(trim((get_post_meta($id, '_arka_from', true) ? 'от ' : '') . get_post_meta($id, '_arka_price', true) . ' ' . get_post_meta($id, '_arka_unit', true)));
	if ($col === 'order') echo (int) get_post_field('menu_order', $id);
}, 10, 2);
add_filter('manage_arka_faq_posts_columns', fn($c) => array_slice($c, 0, 2) + ['order' => 'Порядок'] + $c);
add_action('manage_arka_faq_posts_custom_column', function ($col, $id) { if ($col === 'order') echo (int) get_post_field('menu_order', $id); }, 10, 2);
add_action('pre_get_posts', function ($q) {
	if (is_admin() && $q->is_main_query() && in_array($q->get('post_type'), ['arka_format', 'arka_faq'], true) && !$q->get('orderby')) {
		$q->set('orderby', 'menu_order'); $q->set('order', 'ASC');
	}
});

function arka_formats() {
	return get_posts(['post_type' => 'arka_format', 'numberposts' => 20, 'orderby' => 'menu_order', 'order' => 'ASC', 'post_status' => 'publish']);
}
function arka_format_img($p) {
	if (has_post_thumbnail($p)) return get_the_post_thumbnail_url($p, 'large');
	$f = get_post_meta($p->ID, '_arka_img', true) ?: 'ph-conf.jpg';
	return ARKA_URI . '/assets/' . rawurlencode(basename($f));
}

/* страница «Форматы»: навигация-чипы */
function arka_formats_nav() {
	foreach (arka_formats() as $p) echo '<a href="#' . esc_attr($p->post_name) . '">' . esc_html(get_the_title($p)) . '</a>';
}
/* страница «Форматы»: блоки с фото, текстом, ценой и кнопкой */
function arka_formats_full() {
	foreach (arka_formats() as $p) {
		$m = fn($k) => get_post_meta($p->ID, $k, true);
		$id = esc_attr($p->post_name);
		$key = $m('_arka_key') ?: get_the_title($p);
		$href = add_query_arg('f', rawurlencode($key), home_url('/')) . '#book-s';
		$bul = array_filter(array_map('trim', explode("\n", (string) $m('_arka_bullets'))));
		?>
		<article class="fmt" id="<?php echo $id; ?>" aria-labelledby="<?php echo $id; ?>-h">
			<div class="fmt-ph"><img src="<?php echo esc_url(arka_format_img($p)); ?>" alt="<?php echo esc_attr($m('_arka_alt')); ?>" loading="lazy"></div>
			<div class="fmt-tx">
				<h2 class="h-sec" id="<?php echo $id; ?>-h"><?php echo esc_html(get_the_title($p)); ?></h2>
				<div class="t-body-l"><?php echo wp_kses_post(wpautop($p->post_content)); ?></div>
				<?php if ($bul) : ?><ul><?php foreach ($bul as $b) echo '<li><span class="msi">check</span>' . esc_html($b) . '</li>'; ?></ul><?php endif; ?>
				<div class="fmt-price"><b><?php echo esc_html(($m('_arka_from') ? 'от ' : '') . $m('_arka_price')); ?> <small><?php echo esc_html($m('_arka_unit')); ?></small></b><span class="t-small"><?php echo esc_html($m('_arka_note')); ?></span></div>
				<div class="btns"><a class="btn btn-filled" href="<?php echo esc_url($href); ?>"><?php echo esc_html($m('_arka_cta') ?: 'Забронировать'); ?><span class="msi">arrow_forward</span></a></div>
			</div>
		</article>
		<?php
	}
}

/* вопросы: на главной первые $limit, на странице вопросов все */
function arka_faq_list($limit = -1) {
	$qs = get_posts(['post_type' => 'arka_faq', 'numberposts' => $limit, 'orderby' => 'menu_order', 'order' => 'ASC', 'post_status' => 'publish']);
	foreach ($qs as $i => $q) {
		printf('<details class="qa"%s><summary>%s<span class="msi">expand_more</span></summary>%s</details>',
			$i === 0 ? ' open' : '', esc_html(get_the_title($q)), '<p>' . wp_kses(trim(strip_tags($q->post_content, '<a><b><strong><em><br>')), ['a' => ['href' => []], 'b' => [], 'strong' => [], 'em' => [], 'br' => []]) . '</p>');
	}
}
