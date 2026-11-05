<?php
/**
 * АРКА 123: тема WordPress.
 * inc/options.php   настройки «АРКА 123» (контакты, часы, цены, уведомления)
 * inc/content.php   записи «Форматы» и «Вопросы», которые правятся в админке
 * inc/requests.php  заявки и брони: REST API для календаря, список заявок, подтверждение, уведомления, .ics
 * inc/setup.php     подключение стилей и скриптов, меню, первичное наполнение при активации темы
 */
defined('ABSPATH') || exit;

define('ARKA_VER', '1.0.0');
define('ARKA_DIR', get_template_directory());
define('ARKA_URI', get_template_directory_uri());

require ARKA_DIR . '/inc/options.php';
require ARKA_DIR . '/inc/content.php';
require ARKA_DIR . '/inc/requests.php';
require ARKA_DIR . '/inc/setup.php';
