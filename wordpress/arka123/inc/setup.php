<?php
/* Подключение файлов, меню и первичное наполнение сайта при активации темы. */
defined('ABSPATH') || exit;

add_action('after_setup_theme', function () {
	add_theme_support('title-tag');
	add_theme_support('post-thumbnails');
	add_theme_support('html5', ['script', 'style', 'navigation-widgets']);
	register_nav_menus(['primary' => 'Шапка сайта']);
	add_post_type_support('page', 'excerpt');
});

/* блоки, которые менеджер добавил в редакторе страницы, выводятся под основной вёрсткой */
function arka_page_content() {
	if (!trim(get_post_field('post_content', get_the_ID()))) return;
	echo '<section class="w sec"><div class="prose">';
	the_content();
	echo '</div></section>';
}

/* адреса страниц по ярлыку: arka_url('zal') */
function arka_url($slug = '') {
	if ($slug === '') return home_url('/');
	$p = get_page_by_path($slug);
	return $p ? get_permalink($p) : home_url('/' . $slug . '/');
}
function arka_asset($f) { return ARKA_URI . '/assets/' . $f; }
function arka_book_url() { return is_front_page() ? '#book-s' : home_url('/') . '#book-s'; }

add_action('wp_enqueue_scripts', function () {
	$icons = 'account_balance,add,arrow_back,arrow_forward,call,cancel,celebration,chair,check,check_circle,checkroom,chevron_left,chevron_right,close,co_present,coffee,directions_subway,door_front,elevator,event,event_available,expand_more,format_quote,groups,light_mode,local_parking,local_shipping,mail,map,menu,mic,pause,payments,photo_camera,play_arrow,receipt_long,remove,replay,restaurant,route,schedule,send,square_foot,storefront,swap_horiz,videocam,view_in_ar,wifi,window,work';
	wp_enqueue_style('arka-fonts', 'https://fonts.googleapis.com/css2?family=Roboto+Flex:opsz,wght@8..144,400;8..144,500;8..144,600&family=Roboto:wght@400;500&display=swap', [], null);
	wp_enqueue_style('arka-icons', 'https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0&icon_names=' . $icons . '&display=block', [], null);
	wp_enqueue_style('arka', arka_asset('styles.css'), [], (string) filemtime(ARKA_DIR . '/assets/styles.css'));
	wp_enqueue_script('gsap', arka_asset('gsap.min.js'), [], '3', true);
	wp_enqueue_script('arka-logo', arka_asset('arka-logo.js'), ['gsap'], ARKA_VER, true);
	wp_enqueue_script('arka-site', arka_asset('site.js'), ['arka-logo'], (string) filemtime(ARKA_DIR . '/assets/site.js'), true);
	wp_add_inline_script('arka-site', 'window.ARKA_CFG=' . wp_json_encode([
		'api' => untrailingslashit(rest_url('arka/v1')), 'open' => (int) arka_opt('open'), 'close' => (int) arka_opt('close'),
		'priceDay' => (int) arka_opt('price_day'), 'priceEvening' => (int) arka_opt('price_evening'), 'eveningFrom' => (int) arka_opt('evening_from'),
	]) . ';', 'before');
	$loader = is_front_page() ? 'ArkaLogo.runLoader(l,{counter:l.querySelector("#arkaCount"),reveal:document.querySelector(".hero"),minTime:1400}).then(()=>{try{hdr.intro()}catch(e){}});' : '';
	wp_add_inline_script('arka-logo', '(function(){const l=document.getElementById("loader"),hl=document.querySelector(".logo");if(!window.gsap||!window.ArkaLogo){if(l)l.remove();return}const hdr=ArkaLogo.mount(hl,{mark:true});hdr.bindHover(hl);' . $loader . '})();');
});
add_action('wp_head', function () {
	echo '<meta name="theme-color" content="#213641">' . "\n";
	if (!has_site_icon()) { $u = get_template_directory_uri() . '/assets/'; echo '<link rel="icon" href="' . esc_url($u . 'favicon.ico') . '" sizes="32x32">' . "\n" . '<link rel="icon" href="' . esc_url($u . 'favicon.svg') . '" type="image/svg+xml">' . "\n" . '<link rel="apple-touch-icon" href="' . esc_url($u . 'apple-touch-icon.png') . '">' . "\n"; }
	if (is_front_page()) echo '<script>try{if(sessionStorage.getItem("arka_visited")==="1"&&location.hash!=="#intro")document.documentElement.classList.add("arka-skip")}catch(e){}</script>' . "\n";
}, 1);
/* описание страницы для поисковиков: отрывок страницы, иначе общее */
add_action('wp_head', function () {
	$d = is_singular() && has_excerpt() ? get_the_excerpt() : 'Светлый зал 123 м² с арочными окнами 4 × 3,5 м напротив Национальной библиотеки. Почасовая аренда, ' . arka_opt('address') . '.';
	echo '<meta name="description" content="' . esc_attr(wp_strip_all_tags($d)) . '">' . "\n";
}, 2);
add_filter('show_admin_bar', '__return_false');

/* пункты шапки: меню «Шапка сайта» из админки, если не задано, то стандартный набор */
function arka_nav_items() {
	$loc = get_nav_menu_locations();
	if (!empty($loc['primary']) && ($items = wp_get_nav_menu_items($loc['primary']))) {
		return array_map(fn($i) => ['url' => $i->url, 'title' => $i->title, 'cur' => (int) $i->object_id === get_queried_object_id() && $i->object === 'page'], $items);
	}
	$out = [];
	foreach (['zal' => 'Зал', 'formaty' => 'Форматы', 'ceny' => 'Цены', 'voprosy' => 'Вопросы', 'kontakty' => 'Контакты'] as $s => $t) $out[] = ['url' => arka_url($s), 'title' => $t, 'cur' => is_page($s)];
	return $out;
}

/* хлебные крошки и шапка внутренней страницы */
function arka_crumbs($title) {
	echo '<nav class="crumbs" aria-label="Вы здесь"><a href="' . esc_url(home_url('/')) . '">Главная</a><span aria-hidden="true">/</span><span aria-current="page">' . esc_html($title) . '</span></nav>';
}
function arka_next($slug, $label) {
	$href = $slug === '#book' ? home_url('/') . '#book-s' : arka_url($slug);
	echo '<section class="w sec"><a class="nextp" href="' . esc_url($href) . '"><span><small>Дальше</small><b>' . esc_html($label) . '</b></span><span class="msi">arrow_forward</span></a></section>';
}
function arka_mascot($name) { include ARKA_DIR . '/template-parts/ark-' . $name . '.svg'; }

/* ---------- первичное наполнение: страницы, меню, форматы, вопросы ---------- */
add_action('after_switch_theme', 'arka_seed');
function arka_seed() {
	require_once ARKA_DIR . '/inc/seed.php';
	$ids = [];
	foreach (arka_seed_pages() as $slug => [$title, $content, $excerpt]) {
		$p = get_page_by_path($slug);
		$ids[$slug] = $p ? $p->ID : wp_insert_post(['post_type' => 'page', 'post_status' => 'publish', 'post_name' => $slug, 'post_title' => $title, 'post_content' => $content, 'post_excerpt' => $excerpt]);
	}
	if (!get_option('page_on_front') || get_option('show_on_front') !== 'page') { update_option('show_on_front', 'page'); update_option('page_on_front', $ids['glavnaya']); }
	if (!get_option('permalink_structure')) { update_option('permalink_structure', '/%postname%/'); }
	flush_rewrite_rules();

	if (!get_posts(['post_type' => 'arka_format', 'numberposts' => 1, 'post_status' => 'any'])) {
		foreach (arka_seed_formats() as $i => $f) {
			$id = wp_insert_post(['post_type' => 'arka_format', 'post_status' => 'publish', 'post_name' => $f['slug'], 'post_title' => $f['title'], 'post_content' => $f['text'], 'menu_order' => $i]);
			foreach (['price', 'unit', 'from', 'note', 'bullets', 'key', 'cta', 'img', 'alt'] as $k) update_post_meta($id, '_arka_' . $k, $f[$k]);
		}
	}
	if (!get_posts(['post_type' => 'arka_faq', 'numberposts' => 1, 'post_status' => 'any'])) {
		foreach (arka_seed_faq() as $i => [$q, $a]) wp_insert_post(['post_type' => 'arka_faq', 'post_status' => 'publish', 'post_title' => $q, 'post_content' => $a, 'menu_order' => $i]);
	}
	$locs = get_nav_menu_locations();
	if (empty($locs['primary'])) {
		$menu = wp_get_nav_menu_object('Шапка сайта') ?: wp_get_nav_menu_object(wp_create_nav_menu('Шапка сайта'));
		if ($menu && !wp_get_nav_menu_items($menu->term_id)) {
			$i = 0;
			foreach (arka_seed_menu() as $s => $label) wp_update_nav_menu_item($menu->term_id, 0, ['menu-item-object-id' => $ids[$s], 'menu-item-object' => 'page', 'menu-item-type' => 'post_type', 'menu-item-title' => $label, 'menu-item-status' => 'publish', 'menu-item-position' => ++$i]);
		}
		if ($menu) { $locs['primary'] = $menu->term_id; set_theme_mod('nav_menu_locations', $locs); }
	}
	$o = (array) get_option('arka_options', []);
	if (empty($o['ics_key'])) { $o['ics_key'] = wp_generate_password(20, false); update_option('arka_options', $o); }
}
