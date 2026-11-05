<?php
/* Настройки «АРКА 123»: одна страница в админке, все поля в одной опции arka_options. */
defined('ABSPATH') || exit;

function arka_defaults() {
	return [
		'phone'          => '+375 29 123-01-23',
		'phone_note'     => 'Звонок, WhatsApp, Viber · 9:00–21:00',
		'telegram'       => 'arka123_minsk',
		'manager'        => 'Анна',
		'email'          => 'hello@arka123.by',
		'address'        => 'Минск, ул. Мстиславца, 10, второй этаж',
		'company'        => 'ООО «Арка Сто Двадцать Три»',
		'unp'            => '193000123',
		'open'           => 9,
		'close'          => 21,
		'evening_from'   => 17,
		'price_day'      => 90,
		'price_evening'  => 120,
		'hold_hours'     => 24,
		'notify_email'   => '',
		'tg_token'       => '',
		'tg_chat'        => '',
		'webhook_url'    => '',
		'webhook_secret' => '',
		'ics_key'        => '',
	];
}

function arka_opt($key) {
	static $o = null;
	if ($o === null) $o = wp_parse_args((array) get_option('arka_options', []), arka_defaults());
	return $o[$key] ?? '';
}
function arka_tel() { return 'tel:' . preg_replace('/[^\d+]/', '', arka_opt('phone')); }

/* Поля страницы настроек: ключ => [подпись, тип, подсказка] */
function arka_fields() {
	return [
		'Контакты на сайте' => [
			'phone'      => ['Телефон', 'text', 'Показывается в шапке, подвале и на странице контактов'],
			'phone_note' => ['Подпись к телефону', 'text', ''],
			'telegram'   => ['Telegram менеджера', 'text', 'Без @, например arka123_minsk'],
			'manager'    => ['Имя менеджера', 'text', 'В тексте «Анна ответит в Telegram в течение 15 минут»'],
			'email'      => ['E-mail', 'email', ''],
			'address'    => ['Адрес', 'text', ''],
			'company'    => ['Юрлицо', 'text', ''],
			'unp'        => ['УНП', 'text', ''],
		],
		'Календарь и цены' => [
			'open'          => ['Открываемся, час', 'number', 'Первый час, который можно забронировать'],
			'close'         => ['Закрываемся, час', 'number', 'Бронь должна закончиться до этого часа'],
			'evening_from'  => ['Вечерний тариф с, час', 'number', ''],
			'price_day'     => ['Час днём, BYN', 'number', ''],
			'price_evening' => ['Час вечером и в выходные, BYN', 'number', ''],
			'hold_hours'    => ['Держать неподтверждённую бронь, часов', 'number', 'Потом время освобождается само'],
		],
		'Уведомления о заявках' => [
			'notify_email'   => ['Письмо на адрес', 'email', 'Пусто: адрес администратора сайта'],
			'tg_token'       => ['Токен Telegram-бота', 'text', 'Необязательно. Бот пришлёт заявку в чат'],
			'tg_chat'        => ['ID чата Telegram', 'text', ''],
			'webhook_url'    => ['Вебхук (Zapier, Make, n8n)', 'url', 'POST с JSON при создании, подтверждении и отмене'],
			'webhook_secret' => ['Секрет вебхука', 'text', 'Уходит в заголовке X-Arka-Secret'],
		],
	];
}

add_action('admin_menu', function () {
	add_menu_page('АРКА 123', 'АРКА 123', 'manage_options', 'arka-settings', 'arka_settings_page', 'dashicons-building', 3);
});

add_action('admin_init', function () {
	register_setting('arka', 'arka_options', ['sanitize_callback' => 'arka_sanitize_options']);
});

function arka_sanitize_options($in) {
	$out = (array) get_option('arka_options', []);
	foreach (arka_fields() as $group) foreach ($group as $k => $f) {
		if (!isset($in[$k])) continue;
		$v = $in[$k];
		$out[$k] = $f[1] === 'number' ? max(0, min(1000000, (int) $v)) : ($f[1] === 'email' ? sanitize_email($v) : ($f[1] === 'url' ? esc_url_raw($v) : sanitize_text_field($v)));
	}
	$out['open']  = max(0, min(22, (int) ($out['open'] ?? 9)));
	$out['close'] = max($out['open'] + 2, min(24, (int) ($out['close'] ?? 21)));
	/* «Сменить адрес календаря»: старая ссылка подписки перестаёт работать */
	if (empty($out['ics_key']) || !empty($in['ics_reset'])) $out['ics_key'] = wp_generate_password(32, false);
	return $out;
}

function arka_settings_page() {
	if (!current_user_can('manage_options')) return;
	$o = wp_parse_args((array) get_option('arka_options', []), arka_defaults());
	if (empty($o['ics_key'])) { $o['ics_key'] = wp_generate_password(20, false); update_option('arka_options', $o); }
	$ics = add_query_arg(['arka-ics' => $o['ics_key']], home_url('/'));
	?>
	<div class="wrap">
		<h1>АРКА 123: настройки сайта</h1>
		<p>Тексты страниц меняются в разделе «Страницы», форматы и вопросы в одноимённых разделах меню, заявки в «Заявках».</p>
		<form method="post" action="options.php">
			<?php settings_fields('arka'); ?>
			<?php foreach (arka_fields() as $title => $group) : ?>
				<h2><?php echo esc_html($title); ?></h2>
				<table class="form-table" role="presentation">
				<?php foreach ($group as $k => [$label, $type, $hint]) : ?>
					<tr><th scope="row"><label for="arka-<?php echo esc_attr($k); ?>"><?php echo esc_html($label); ?></label></th>
					<td><input class="regular-text" type="<?php echo esc_attr($type); ?>" id="arka-<?php echo esc_attr($k); ?>" name="arka_options[<?php echo esc_attr($k); ?>]" value="<?php echo esc_attr($o[$k]); ?>">
					<?php if ($hint) echo '<p class="description">' . esc_html($hint) . '</p>'; ?></td></tr>
				<?php endforeach; ?>
				</table>
			<?php endforeach; ?>
			<input type="hidden" name="arka_options[ics_key]" value="<?php echo esc_attr($o['ics_key']); ?>">
			<?php submit_button('Сохранить'); ?>
		</form>
		<h2>Подписка на календарь броней</h2>
		<p>Добавьте этот адрес в Google Календарь («Другие календари» → «Из URL»), Apple или Outlook. Адрес секретный, не публикуйте его.</p>
		<p><input class="large-text code" readonly value="<?php echo esc_attr($ics); ?>" onclick="this.select()"></p>
		<form method="post" action="options.php"><?php settings_fields('arka'); ?><input type="hidden" name="arka_options[ics_reset]" value="1">
			<?php submit_button('Сменить адрес календаря', 'secondary', 'submit', false, ['onclick' => "return confirm('Старая ссылка подписки перестанет работать. Сменить?')"]); ?></form>
	</div>
	<?php
}
