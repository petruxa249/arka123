<?php
/*
 * Заявки и брони.
 * REST:  GET  /wp-json/arka/v1/availability  занятые часы по датам (для календаря на сайте)
 *        POST /wp-json/arka/v1/requests      новая заявка: проверка, пересечения, сохранение, уведомления
 * Админка: «Заявки» со статусами (новая, подтверждена, отменена), подтверждение в один клик, фильтры,
 *          счётчик новых в меню, «Календарь броней» на 14 дней, виджет на консоли, подписка .ics.
 * Неподтверждённая бронь держит время arka_opt('hold_hours') часов, подтверждённая насовсем.
 */
defined('ABSPATH') || exit;

const ARKA_TZ = 'Europe/Minsk';
const ARKA_CHANNELS = ['Telegram', 'WhatsApp', 'Viber', 'звонок', 'E-mail'];
const ARKA_STATUSES = ['new' => 'Новая', 'confirmed' => 'Подтверждена', 'cancelled' => 'Отменена'];

add_action('init', function () {
	register_post_type('arka_request', [
		'labels' => ['name' => 'Заявки', 'singular_name' => 'Заявка', 'edit_item' => 'Заявка', 'all_items' => 'Все заявки', 'search_items' => 'Найти заявку', 'not_found' => 'Заявок пока нет'],
		'public' => false, 'show_ui' => true, 'menu_icon' => 'dashicons-calendar-alt', 'menu_position' => 4,
		'supports' => ['title'], 'capability_type' => ['arka_request', 'arka_requests'], 'capabilities' => ['create_posts' => 'do_not_allow'], 'map_meta_cap' => true,
	]);
	/* заявки с телефонами гостей видят только администратор и редактор, а не авторы и участники */
	if (get_option('arka_caps_ver') !== '1') {
		$caps = ['edit_arka_requests', 'edit_others_arka_requests', 'edit_published_arka_requests', 'edit_private_arka_requests', 'publish_arka_requests',
			'read_private_arka_requests', 'delete_arka_requests', 'delete_others_arka_requests', 'delete_published_arka_requests', 'delete_private_arka_requests'];
		foreach (['administrator', 'editor'] as $role) if ($r = get_role($role)) foreach ($caps as $c) $r->add_cap($c);
		update_option('arka_caps_ver', '1');
	}
});
const ARKA_CAP = 'edit_others_arka_requests';

/* ---------- время и данные ---------- */
function arka_now() {
	$d = new DateTime('now', new DateTimeZone(ARKA_TZ));
	return ['date' => $d->format('Y-m-d'), 'hour' => (int) $d->format('G')];
}
function arka_add_days($iso, $n) { $d = new DateTime($iso . ' 00:00:00', new DateTimeZone('UTC')); $d->modify(($n >= 0 ? '+' : '') . $n . ' days'); return $d->format('Y-m-d'); }
function arka_valid_date($s) { if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $s)) return false; [$y, $m, $d] = array_map('intval', explode('-', $s)); return checkdate($m, $d, $y); }
function arka_price($start, $dur) { $s = 0; for ($h = $start; $h < $start + $dur; $h++) $s += $h >= (int) arka_opt('evening_from') ? (int) arka_opt('price_evening') : (int) arka_opt('price_day'); return $s; }

function arka_req($id) {
	$m = fn($k) => get_post_meta($id, '_arka_' . $k, true);
	$r = ['id' => $id, 'name' => $m('name'), 'contact' => $m('contact'), 'channel' => $m('channel'), 'format' => $m('format'), 'guests' => (int) $m('guests'),
	      'message' => $m('message'), 'status' => $m('status') ?: 'new', 'created' => (int) $m('created'), 'booking' => null];
	if ($m('date')) $r['booking'] = ['date' => $m('date'), 'start' => (int) $m('start'), 'dur' => (int) $m('dur'), 'price' => (int) $m('price')];
	return $r;
}
function arka_is_active($r) {
	if (!$r['booking']) return false;
	return $r['status'] === 'confirmed' || ($r['status'] === 'new' && time() - $r['created'] < (int) arka_opt('hold_hours') * 3600);
}
function arka_bookings($from, $to) {
	$ids = get_posts(['post_type' => 'arka_request', 'post_status' => 'any', 'numberposts' => -1, 'fields' => 'ids',
		'meta_query' => [['key' => '_arka_date', 'value' => [$from, $to], 'compare' => 'BETWEEN', 'type' => 'CHAR']]]);
	update_meta_cache('post', $ids); /* одна выборка мета-полей вместо девяти запросов на каждую бронь */
	return array_map('arka_req', $ids);
}
function arka_busy($from, $to) {
	$busy = [];
	foreach (arka_bookings($from, $to) as $r) {
		if (!arka_is_active($r)) continue;
		$b = $r['booking'];
		for ($h = $b['start']; $h < $b['start'] + $b['dur']; $h++) $busy[$b['date']][] = $h;
	}
	return (object) $busy;
}

/* ---------- REST ---------- */
add_action('rest_api_init', function () {
	register_rest_route('arka/v1', '/availability', ['methods' => 'GET', 'permission_callback' => '__return_true', 'callback' => function (WP_REST_Request $q) {
		$now = arka_now();
		$from = (string) ($q->get_param('from') ?: $now['date']); $to = (string) ($q->get_param('to') ?: arka_add_days($now['date'], 180));
		if (!arka_valid_date($from) || !arka_valid_date($to)) return new WP_REST_Response(['error' => 'Неверные даты'], 400);
		if ($from < $now['date']) $from = $now['date'];
		$res = new WP_REST_Response(['today' => $now['date'], 'hour' => $now['hour'], 'open' => (int) arka_opt('open'), 'close' => (int) arka_opt('close'), 'busy' => arka_busy($from, $to)]);
		$res->header('Cache-Control', 'no-store');
		return $res;
	}]);
	register_rest_route('arka/v1', '/requests', ['methods' => 'POST', 'permission_callback' => '__return_true', 'callback' => 'arka_rest_create']);
});

function arka_contact_key($c) { $d = preg_replace('/\D/', '', (string) $c); return strlen($d) >= 7 ? substr($d, -9) : ltrim(mb_strtolower((string) $c), '@'); }
function arka_clean($v, $max) { return mb_substr(trim(preg_replace('/[\x00-\x1f]/u', ' ', (string) $v)), 0, $max); }

function arka_rest_create(WP_REST_Request $q) {
	$err = fn($m, $code = 400) => new WP_REST_Response(['error' => $m], $code);
	/* не более 8 заявок за 10 минут с одного адреса */
	$ipk = 'arka_rl_' . md5($_SERVER['REMOTE_ADDR'] ?? '');
	$hits = array_filter((array) get_transient($ipk), fn($t) => time() - $t < 600);
	$hits[] = time(); set_transient($ipk, $hits, 600);
	if (count($hits) > 8) return $err('Слишком много заявок, попробуйте через несколько минут', 429);

	$b = $q->get_json_params() ?: [];
	if (arka_clean($b['website'] ?? '', 50) !== '') return $err('Спам-фильтр');
	$name = arka_clean($b['name'] ?? '', 80); $contact = arka_clean($b['contact'] ?? '', 120);
	if (mb_strlen($name) < 2) return $err('Введите имя');
	if (mb_strlen($contact) < 3) return $err('Укажите, как с вами связаться');
	$channel = in_array($b['channel'] ?? '', ARKA_CHANNELS, true) ? $b['channel'] : 'Telegram';
	if ($channel === 'E-mail' && !is_email($contact)) return $err('Проверьте адрес почты');
	if (in_array($channel, ['WhatsApp', 'Viber', 'звонок'], true) && strlen(preg_replace('/\D/', '', $contact)) < 7) return $err('Проверьте номер телефона');
	$rec = ['name' => $name, 'contact' => $contact, 'channel' => $channel,
		'format' => arka_clean($b['format'] ?? '', 40), 'guests' => max(0, min(500, (int) ($b['guests'] ?? 0))), 'message' => arka_clean($b['message'] ?? '', 500)];

	$open = (int) arka_opt('open'); $close = (int) arka_opt('close');
	if (!empty($b['booking']) && is_array($b['booking'])) {
		$now = arka_now(); $date = (string) ($b['booking']['date'] ?? ''); $start = $b['booking']['start'] ?? null; $dur = $b['booking']['dur'] ?? null;
		if (!arka_valid_date($date) || $date < $now['date'] || $date > arka_add_days($now['date'], 180)) return $err('Недопустимая дата');
		if (!is_int($start) || !is_int($dur) || $start < $open || $dur < 2 || $start + $dur > $close) return $err('Недопустимое время');
		if ($date === $now['date'] && $start <= $now['hour']) return $err('Это время уже прошло');
		$rec['date'] = $date; $rec['start'] = $start; $rec['dur'] = $dur; $rec['price'] = arka_price($start, $dur);
	}

	/* проверка пересечений и запись под замком: две одновременные заявки не займут один час.
	   Замок не взят за 3 секунды: заявка не пишется вслепую, гость получает «попробуйте ещё раз». */
	$lock = 'arka_booking_lock'; $got = false;
	for ($i = 0; $i < 30; $i++) {
		if (add_option($lock, time(), '', 'no')) { $got = true; break; }
		wp_cache_delete($lock, 'options'); wp_cache_delete('notoptions', 'options');
		if (time() - (int) get_option($lock) > 10) delete_option($lock);
		usleep(100000);
	}
	if (!$got) return $err('Сервер занят, попробуйте ещё раз через пару секунд', 503);
	$rec['iph'] = substr(hash_hmac('sha256', $_SERVER['REMOTE_ADDR'] ?? '', wp_salt('nonce')), 0, 16); /* хэш адреса, не сам адрес */
	try {
		if (isset($rec['date'])) {
			/* не больше 3 неподтверждённых броней с одного адреса или контакта: иначе один человек займёт весь календарь */
			$ck = arka_contact_key($contact); $holds = 0;
			foreach (arka_bookings(arka_now()['date'], arka_add_days(arka_now()['date'], 180)) as $o)
				if ($o['status'] === 'new' && arka_is_active($o) && (get_post_meta($o['id'], '_arka_iph', true) === $rec['iph'] || arka_contact_key($o['contact']) === $ck)) $holds++;
			if ($holds >= 3) return $err('У вас уже есть неподтверждённые брони. Дождитесь ответа менеджера или позвоните нам', 429);
			$busy = (array) arka_busy($rec['date'], $rec['date']);
			$taken = $busy[$rec['date']] ?? [];
			for ($h = $rec['start']; $h < $rec['start'] + $rec['dur']; $h++) if (in_array($h, $taken, true)) return $err('Это время уже заняли, выберите другое', 409);
		}
		$title = $name . (isset($rec['date']) ? ' · ' . $rec['date'] . ' ' . $rec['start'] . ':00–' . ($rec['start'] + $rec['dur']) . ':00' : ' · без даты');
		$id = wp_insert_post(['post_type' => 'arka_request', 'post_status' => 'publish', 'post_title' => $title], true);
		if (is_wp_error($id)) return $err('Не удалось сохранить заявку', 500);
		foreach ($rec + ['status' => 'new', 'created' => time()] as $k => $v) update_post_meta($id, '_arka_' . $k, $v);
	} finally { delete_option($lock); }

	$r = arka_req($id);
	arka_notify($r);
	arka_hook('request.created', $r);
	return new WP_REST_Response(['ok' => true, 'id' => $id, 'booking' => $r['booking']], 201);
}

/* ---------- уведомления ---------- */
function arka_text($r) {
	$b = $r['booking'];
	return "{$r['name']} · {$r['channel']}: {$r['contact']}\n" . ($b ? "Бронь: {$b['date']}, {$b['start']}:00–" . ($b['start'] + $b['dur']) . ":00, {$b['price']} BYN\n" : "Без даты\n")
		. 'Формат: ' . ($r['format'] ?: '—') . ', гостей: ' . ($r['guests'] ?: '—') . ($r['message'] ? "\n{$r['message']}" : '');
}
function arka_notify($r) {
	$to = arka_opt('notify_email') ?: get_option('admin_email');
	$link = admin_url('post.php?post=' . $r['id'] . '&action=edit');
	wp_mail($to, 'Новая заявка АРКА 123: ' . $r['name'], arka_text($r) . "\n\nОткрыть: $link");
	if (arka_opt('tg_token') && arka_opt('tg_chat')) {
		wp_remote_post('https://api.telegram.org/bot' . arka_opt('tg_token') . '/sendMessage', ['blocking' => false, 'timeout' => 3,
			'headers' => ['Content-Type' => 'application/json'], 'body' => wp_json_encode(['chat_id' => arka_opt('tg_chat'), 'text' => "Новая заявка АРКА 123\n" . arka_text($r)])]);
	}
}
function arka_iso($date, $h) { return sprintf('%sT%02d:00:00+03:00', $date, $h); }
function arka_hook($event, $r) {
	if (!arka_opt('webhook_url')) return;
	$b = $r['booking'];
	if ($b) $b += ['startISO' => arka_iso($b['date'], $b['start']), 'endISO' => arka_iso($b['date'], $b['start'] + $b['dur']), 'summary' => 'АРКА 123: ' . $r['name'] . ' (' . ($r['format'] ?: 'аренда') . ')'];
	$body = wp_json_encode(['event' => $event] + array_merge($r, ['booking' => $b]));
	$ts = (string) time(); $secret = (string) arka_opt('webhook_secret');
	$headers = ['Content-Type' => 'application/json', 'X-Arka-Event' => $event, 'X-Arka-Timestamp' => $ts];
	/* подпись HMAC: получатель проверяет X-Arka-Signature и возраст метки; X-Arka-Secret оставлен для простых сервисов */
	if ($secret !== '') $headers += ['X-Arka-Signature' => 'sha256=' . hash_hmac('sha256', $ts . '.' . $body, $secret), 'X-Arka-Secret' => $secret];
	/* wp_safe_remote_post не пускает запрос на localhost и внутренние адреса сервера */
	wp_safe_remote_post(arka_opt('webhook_url'), ['blocking' => false, 'timeout' => 3, 'headers' => $headers, 'body' => $body]);
}

/* ---------- смена статуса ---------- */
function arka_set_status($id, $st) {
	if (!isset(ARKA_STATUSES[$st]) || get_post_type($id) !== 'arka_request') return;
	update_post_meta($id, '_arka_status', $st);
	arka_hook($st === 'confirmed' ? 'request.confirmed' : ($st === 'cancelled' ? 'request.cancelled' : 'request.updated'), arka_req($id));
}
function arka_status_label($r) {
	if ($r['status'] === 'new' && $r['booking'] && !arka_is_active($r)) return ['expired', 'Истекла'];
	return [$r['status'], ARKA_STATUSES[$r['status']] ?? $r['status']];
}

/* ---------- список заявок ---------- */
add_filter('manage_arka_request_posts_columns', function () {
	return ['cb' => '<input type="checkbox">', 'title' => 'Гость', 'arka_when' => 'Дата и время', 'arka_contact' => 'Связь', 'arka_format' => 'Формат', 'arka_sum' => 'Сумма', 'arka_status' => 'Статус', 'date' => 'Получена'];
});
add_action('manage_arka_request_posts_custom_column', function ($col, $id) {
	$r = arka_req($id); $b = $r['booking'];
	switch ($col) {
		case 'arka_when': echo $b ? esc_html(date_i18n('j F, D', strtotime($b['date'])) . ' · ' . $b['start'] . ':00–' . ($b['start'] + $b['dur']) . ':00') : '<span style="color:#888">без даты</span>'; break;
		case 'arka_contact': echo esc_html($r['channel'] . ': ' . $r['contact']); break;
		case 'arka_format': echo esc_html(($r['format'] ?: '—') . ($r['guests'] ? ', ' . $r['guests'] . ' гостей' : '')); if ($r['message']) echo '<br><small>' . esc_html($r['message']) . '</small>'; break;
		case 'arka_sum': echo $b ? esc_html(number_format_i18n($b['price']) . ' BYN') : '—'; break;
		case 'arka_status': [$k, $l] = arka_status_label($r); echo '<span class="arka-st arka-st-' . esc_attr($k) . '">' . esc_html($l) . '</span>'; break;
	}
}, 10, 2);
add_filter('manage_edit-arka_request_sortable_columns', fn($c) => $c + ['arka_when' => 'arka_when']);
add_action('pre_get_posts', function ($q) {
	if (!is_admin() || !$q->is_main_query() || $q->get('post_type') !== 'arka_request') return;
	if ($q->get('orderby') === 'arka_when') { $q->set('meta_key', '_arka_date'); $q->set('orderby', 'meta_value'); }
	$st = sanitize_key($_GET['arka_status'] ?? '');
	if (isset(ARKA_STATUSES[$st])) $q->set('meta_query', [['key' => '_arka_status', 'value' => $st]]);
});
/* вкладки по статусам над списком */
add_filter('views_edit-arka_request', function ($views) {
	$base = admin_url('edit.php?post_type=arka_request'); $cur = sanitize_key($_GET['arka_status'] ?? '');
	$out = ['all' => '<a href="' . esc_url($base) . '"' . ($cur ? '' : ' class="current"') . '>Все</a>'];
	foreach (ARKA_STATUSES as $k => $l) {
		$n = count(get_posts(['post_type' => 'arka_request', 'post_status' => 'any', 'numberposts' => -1, 'fields' => 'ids', 'meta_query' => [['key' => '_arka_status', 'value' => $k]]]));
		$out[$k] = '<a href="' . esc_url(add_query_arg('arka_status', $k, $base)) . '"' . ($cur === $k ? ' class="current"' : '') . '>' . esc_html($l) . ' <span class="count">(' . $n . ')</span></a>';
	}
	return $out;
});
/* действия в строке: подтвердить, отменить */
add_filter('post_row_actions', function ($a, $post) {
	if ($post->post_type !== 'arka_request') return $a;
	unset($a['inline hide-if-no-js']);
	$st = arka_req($post->ID)['status'];
	foreach (['confirmed' => 'Подтвердить', 'cancelled' => 'Отменить'] as $k => $l) {
		if ($st === $k) continue;
		$u = wp_nonce_url(admin_url('admin-post.php?action=arka_status&id=' . $post->ID . '&st=' . $k), 'arka_status_' . $post->ID);
		$a['arka_' . $k] = '<a href="' . esc_url($u) . '">' . esc_html($l) . '</a>';
	}
	return $a;
}, 10, 2);
add_action('admin_post_arka_status', function () {
	$id = (int) ($_GET['id'] ?? 0);
	check_admin_referer('arka_status_' . $id);
	if (!current_user_can('edit_post', $id)) wp_die('Нет прав');
	arka_set_status($id, sanitize_key($_GET['st'] ?? ''));
	wp_safe_redirect(wp_get_referer() ?: admin_url('edit.php?post_type=arka_request'));
	exit;
});
/* массовые действия */
add_filter('bulk_actions-edit-arka_request', fn($a) => ['arka_confirmed' => 'Подтвердить', 'arka_cancelled' => 'Отменить'] + $a);
add_filter('handle_bulk_actions-edit-arka_request', function ($to, $action, $ids) {
	if (strpos($action, 'arka_') !== 0) return $to;
	foreach ($ids as $id) if (current_user_can('edit_post', $id)) arka_set_status((int) $id, substr($action, 5));
	return $to;
}, 10, 3);

/* карточка заявки */
add_action('add_meta_boxes_arka_request', function () {
	remove_meta_box('submitdiv', 'arka_request', 'side');
	add_meta_box('arka-req', 'Заявка', function ($post) {
		$r = arka_req($post->ID); $b = $r['booking']; [$k, $l] = arka_status_label($r);
		wp_nonce_field('arka_req', 'arka_req_nonce');
		$rows = ['Имя' => $r['name'], 'Связь' => $r['channel'] . ': ' . $r['contact'], 'Бронь' => $b ? date_i18n('j F Y, l', strtotime($b['date'])) . ', ' . $b['start'] . ':00–' . ($b['start'] + $b['dur']) . ':00' : 'без даты',
			'Сумма' => $b ? number_format_i18n($b['price']) . ' BYN' : '—', 'Формат' => $r['format'] ?: '—', 'Гостей' => $r['guests'] ?: '—', 'Комментарий' => $r['message'] ?: '—',
			'Получена' => date_i18n('j F Y, H:i', $r['created'] + (int) (get_option('gmt_offset') * 3600))];
		echo '<table class="form-table">';
		foreach ($rows as $t => $v) echo '<tr><th>' . esc_html($t) . '</th><td>' . esc_html($v) . '</td></tr>';
		echo '<tr><th><label for="arka-st">Статус</label></th><td><select id="arka-st" name="arka_status">';
		foreach (ARKA_STATUSES as $sk => $sl) echo '<option value="' . esc_attr($sk) . '"' . selected($r['status'], $sk, false) . '>' . esc_html($sl) . '</option>';
		echo '</select> <span class="arka-st arka-st-' . esc_attr($k) . '">' . esc_html($l) . '</span>';
		echo '<p class="description">Новая бронь держит время ' . (int) arka_opt('hold_hours') . ' ч. Подтверждённая держит его насовсем, отменённая освобождает.</p></td></tr></table>';
		submit_button('Сохранить статус');
	}, 'arka_request', 'normal', 'high');
});
add_action('save_post_arka_request', function ($id) {
	if (!isset($_POST['arka_req_nonce']) || !wp_verify_nonce($_POST['arka_req_nonce'], 'arka_req') || !current_user_can('edit_post', $id)) return;
	$st = sanitize_key($_POST['arka_status'] ?? '');
	if ($st && $st !== arka_req($id)['status']) arka_set_status($id, $st);
});

/* счётчик новых заявок в меню */
add_action('admin_menu', function () {
	global $menu;
	if (!current_user_can(ARKA_CAP)) return;
	$n = count(get_posts(['post_type' => 'arka_request', 'post_status' => 'any', 'numberposts' => -1, 'fields' => 'ids', 'meta_query' => [['key' => '_arka_status', 'value' => 'new']]]));
	if (!$n) return;
	foreach ($menu as &$m) if (($m[2] ?? '') === 'edit.php?post_type=arka_request') $m[0] .= ' <span class="awaiting-mod">' . $n . '</span>';
}, 99);

/* ---------- календарь броней: 14 дней по часам ---------- */
add_action('admin_menu', function () {
	add_submenu_page('edit.php?post_type=arka_request', 'Календарь броней', 'Календарь', ARKA_CAP, 'arka-calendar', 'arka_calendar_page');
});
function arka_calendar_page() {
	if (!current_user_can(ARKA_CAP)) wp_die('Нет прав');
	$now = arka_now(); $start = sanitize_text_field($_GET['from'] ?? $now['date']); if (!arka_valid_date($start)) $start = $now['date'];
	$days = 14; $end = arka_add_days($start, $days - 1); $open = (int) arka_opt('open'); $close = (int) arka_opt('close');
	$cells = [];
	foreach (arka_bookings($start, $end) as $r) {
		if ($r['status'] === 'cancelled' || !arka_is_active($r)) continue;
		$b = $r['booking'];
		for ($h = $b['start']; $h < $b['start'] + $b['dur']; $h++) $cells[$b['date']][$h] = $r;
	}
	$nav = fn($d, $t) => '<a class="button" href="' . esc_url(add_query_arg(['post_type' => 'arka_request', 'page' => 'arka-calendar', 'from' => $d], admin_url('edit.php'))) . '">' . esc_html($t) . '</a>';
	echo '<div class="wrap"><h1>Календарь броней</h1><p>' . $nav(arka_add_days($start, -$days), '← Раньше') . ' ' . $nav($now['date'], 'Сегодня') . ' ' . $nav(arka_add_days($start, $days), 'Позже →') . '</p>';
	echo '<p><span class="arka-cal-key arka-c-confirmed"></span> подтверждена <span class="arka-cal-key arka-c-new"></span> новая, держит время ' . (int) arka_opt('hold_hours') . ' ч</p>';
	echo '<div style="overflow-x:auto"><table class="widefat arka-cal"><thead><tr><th></th>';
	for ($h = $open; $h < $close; $h++) echo '<th>' . $h . ':00</th>';
	echo '</tr></thead><tbody>';
	for ($i = 0; $i < $days; $i++) {
		$d = arka_add_days($start, $i);
		echo '<tr' . ($d === $now['date'] ? ' class="arka-today"' : '') . '><th>' . esc_html(date_i18n('j M, D', strtotime($d))) . '</th>';
		for ($h = $open; $h < $close; $h++) {
			$r = $cells[$d][$h] ?? null;
			if (!$r) { echo '<td></td>'; continue; }
			if ($h > $open && ($cells[$d][$h - 1]['id'] ?? 0) === $r['id']) continue;
			$span = 0; while (($cells[$d][$h + $span]['id'] ?? 0) === $r['id']) $span++;
			echo '<td colspan="' . $span . '" class="arka-c-' . esc_attr($r['status']) . '"><a href="' . esc_url(get_edit_post_link($r['id'])) . '">' . esc_html($r['name']) . '</a><small>' . esc_html($r['format'] ?: '') . '</small></td>';
		}
		echo '</tr>';
	}
	echo '</tbody></table></div></div>';
}

/* виджет на консоли: ближайшие брони */
add_action('wp_dashboard_setup', function () {
	if (!current_user_can(ARKA_CAP)) return;
	wp_add_dashboard_widget('arka_next', 'АРКА 123: ближайшие брони', function () {
		$now = arka_now(); $list = array_filter(arka_bookings($now['date'], arka_add_days($now['date'], 30)), 'arka_is_active');
		usort($list, fn($a, $b) => strcmp($a['booking']['date'] . sprintf('%02d', $a['booking']['start']), $b['booking']['date'] . sprintf('%02d', $b['booking']['start'])));
		if (!$list) { echo '<p>На ближайший месяц броней нет.</p>'; }
		else { echo '<ul>'; foreach (array_slice($list, 0, 8) as $r) { $b = $r['booking']; [$k, $l] = arka_status_label($r);
			echo '<li><a href="' . esc_url(get_edit_post_link($r['id'])) . '"><b>' . esc_html(date_i18n('j M', strtotime($b['date'])) . ', ' . $b['start'] . ':00–' . ($b['start'] + $b['dur']) . ':00') . '</b> ' . esc_html($r['name']) . '</a> <span class="arka-st arka-st-' . esc_attr($k) . '">' . esc_html($l) . '</span></li>'; } echo '</ul>'; }
		echo '<p><a class="button" href="' . esc_url(admin_url('edit.php?post_type=arka_request&page=arka-calendar')) . '">Календарь</a> <a class="button" href="' . esc_url(admin_url('edit.php?post_type=arka_request')) . '">Все заявки</a></p>';
	});
});

add_action('admin_head', function () {
	echo '<style>.arka-st{display:inline-block;padding:2px 8px;border-radius:10px;font-size:12px;line-height:18px;background:#eee}.arka-st-new{background:#fcefd9;color:#7a5726}.arka-st-confirmed{background:#dcefe2;color:#1d5c34}.arka-st-cancelled,.arka-st-expired{background:#eee;color:#777}'
		. '.arka-cal th,.arka-cal td{text-align:center;padding:6px;border-right:1px solid #eee;min-width:56px;white-space:nowrap}.arka-cal tbody th{text-align:left}.arka-cal td small{display:block;opacity:.7}.arka-cal td a{font-weight:600;text-decoration:none}'
		. '.arka-c-confirmed{background:#dcefe2}.arka-c-new{background:#fcefd9}.arka-today th{color:#213641;font-weight:700}.arka-cal-key{display:inline-block;width:14px;height:14px;border-radius:3px;vertical-align:middle;margin:0 4px 0 12px}.arka-cal-key:first-child{margin-left:0}</style>';
});

/* ---------- подписка на календарь (.ics) ---------- */
add_action('init', function () {
	if (!isset($_GET['arka-ics'])) return;
	if (!arka_opt('ics_key') || !hash_equals((string) arka_opt('ics_key'), (string) $_GET['arka-ics'])) { status_header(401); exit('Нужен ключ'); }
	$now = arka_now(); $esc = fn($t) => str_replace(["\\", ';', ',', "\n"], ['\\\\', '\;', '\,', '\n'], (string) $t);
	$utc = fn($d, $h) => gmdate('Ymd\THis\Z', strtotime(arka_iso($d, $h)));
	/* строки длиннее 75 байт переносятся по RFC 5545, иначе Outlook обрезает описание */
	$fold = function ($line) { $out = ''; $n = 0; foreach (preg_split('//u', $line, -1, PREG_SPLIT_NO_EMPTY) as $ch) { $l = strlen($ch); if ($n + $l > 74) { $out .= "\r\n "; $n = 1; } $out .= $ch; $n += $l; } return $out; };
	$out = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//ARKA123//RU', 'CALSCALE:GREGORIAN', 'X-WR-CALNAME:АРКА 123 · брони'];
	foreach (arka_bookings(arka_add_days($now['date'], -30), arka_add_days($now['date'], 180)) as $r) {
		if (!arka_is_active($r)) continue; $b = $r['booking'];
		$out[] = implode("\r\n", array_map($fold, ['BEGIN:VEVENT', 'UID:' . $r['id'] . '@arka123', 'DTSTAMP:' . gmdate('Ymd\THis\Z'), 'DTSTART:' . $utc($b['date'], $b['start']), 'DTEND:' . $utc($b['date'], $b['start'] + $b['dur']),
			'SUMMARY:' . $esc('АРКА 123: ' . $r['name'] . ($r['status'] === 'new' ? ' (не подтверждено)' : '')), 'DESCRIPTION:' . $esc(arka_text($r)), 'END:VEVENT']));
	}
	$out[] = 'END:VCALENDAR';
	header('Content-Type: text/calendar; charset=utf-8'); header('Cache-Control: no-store');
	header('X-Robots-Tag: noindex');
	echo implode("\r\n", $out) . "\r\n"; exit;
});
