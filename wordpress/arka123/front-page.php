<?php
/* Главная: лендинг с первым экраном, бронью, форматами, ценами, заявкой, вопросами и контактами. */
defined('ABSPATH') || exit;
get_header();
the_post();
?>
<section class="hero" aria-labelledby="hero-h">
  <div class="hero-art">
    <img src="<?php echo esc_url(arka_asset('sketch-light.jpg')); ?>" alt="Скетч углового здания АРКА 123, окно второго этажа в форме знака с цифрами 123" width="1280" height="720" fetchpriority="high">
    <video id="heroV" class="hero-v" muted playsinline preload="none" aria-hidden="true"><source src="<?php echo esc_url(arka_asset('flight.webm')); ?>" type="video/webm"><source src="<?php echo esc_url(arka_asset('flight.mp4')); ?>" type="video/mp4"></video>
    <div class="fly-ctl" role="group" aria-label="Пролёт в окно и 3D">
      <button class="fb" type="button" id="flyBtn" aria-label="Остановить видео"><span class="msi" id="flyIc">play_arrow</span><span class="lab" id="flyLab">Пролёт в зал, 6 с</span></button>
      <a class="fb" href="<?php echo esc_url(arka_asset('3d.html')); ?>"><span class="msi">view_in_ar</span><span class="lab">3D-режим</span></a>
    </div>
  </div>
  <div class="w">
    <div class="hero-card">
      <span class="stamp-row"><span>Минск, ул. Мстиславца, 10</span><span>2 этаж</span></span>
      <h1 class="h-display" id="hero-h">АРКА <b>123</b></h1>
      <p class="t-body-l">Светлый зал 123 м² с арочными окнами 4 × 3,5 м напротив Национальной библиотеки. Почасовая аренда для конференций, мастер-классов и съёмок.</p>
      <p class="hero-meta"><span>от <b>90 BYN</b> в час</span><span>до <b>100</b> гостей</span><span><b>7 минут</b> от метро «Восток»</span></p>
    </div>
    <ul class="strip" aria-label="Коротко о зале">
      <li><b>4 × 3,5 м</b><span>два арочных окна на Библиотеку</span></li>
      <li><b>123 м²</b><span>свободная планировка, две колонны</span></li>
      <li><b>4,5 м</b><span>потолки, подвесы для света и декора</span></li>
      <li><b>500 Мбит/с</b><span>Wi-Fi и кабель для трансляций</span></li>
      <li><b>24 часа</b><span>держим дату без предоплаты</span></li>
    </ul>
  </div>
</section>










<section class="w sec" id="book-s" aria-labelledby="book-h">
  <div class="head">
    <h2 class="h-sec" id="book-h">Свободные даты и цена</h2>
  </div>
  <div class="book">
    <div class="ark-col hov">
      <?php arka_mascot('key'); ?>
      <div class="ark-name"><b>Аркадий</b><span id="arkSay">управляющий залом. Держу дату 24 часа без предоплаты.</span></div>
    </div>
    <div class="steps">
      <div class="step" id="st1">
        <div class="step-h"><span class="num" id="n1">1</span><h3 class="t-title">Дата и время</h3><span class="step-sum" id="sum1" hidden></span><button class="btn btn-text" type="button" id="edit1" hidden>Изменить</button></div>
        <div class="step-body" id="b1">
          <div class="grp"><span class="grp-l">Выберите дату</span>
            <div class="chips" id="days"></div>
            <input type="date" id="dOther" tabindex="-1" aria-hidden="true" style="position:absolute;opacity:0;pointer-events:none;width:1px;height:1px"><p class="t-small" id="dOtherNote" style="margin:0" role="status"></p></div>
          <div class="grp rv" id="rvTime"><span class="grp-l" id="timeL">Начало</span>
            <div class="chips" id="times"></div></div>
          <div class="rv" id="rvDur" style="display:grid;gap:24px">
            <div class="grp"><span class="grp-l">Длительность</span>
              <div class="row2"><div class="dur"><button type="button" id="dm" aria-label="Меньше"><span class="msi">remove</span></button><output id="dv">2 часа</output><button type="button" id="dp" aria-label="Больше"><span class="msi">add</span></button></div><span class="t-small">минимум 2 часа, после 17:00 по 120 BYN</span></div></div>
            <div class="total">
              <div><b id="sum">180 BYN</b><span class="t-small" id="sumHint"></span></div>
              <button class="btn btn-filled" type="button" id="next"><span class="d-only" id="nextD">Забронировать</span><span class="m-only">Далее: контакты</span><span class="msi">arrow_forward</span></button>
            </div>
          </div>
        </div>
      </div>
      <div class="step off" id="st2">
        <div class="step-h"><span class="num" id="n2">2</span><h3 class="t-title">Контакты</h3><span class="step-sum" id="sum2h">Откроется после выбора времени</span></div>
        <form class="step-body" id="b2" hidden>
          <input id="hp1" name="website" tabindex="-1" autocomplete="off" aria-hidden="true" style="position:absolute;left:-9999px">
          <div class="fields">
            <div class="field full"><input id="f-name" autocomplete="name" placeholder="Как к вам обращаться"><label for="f-name">Имя</label></div>
            <div class="grp field full rv" id="rvChan" style="gap:12px"><span class="grp-l">Где ответить</span>
              <div class="chips" id="chan">
                <button class="fchip" type="button" data-c="Telegram" data-l="Ник в Telegram" data-p="@username" aria-pressed="false">Telegram</button>
                <button class="fchip" type="button" data-c="WhatsApp" data-l="Номер WhatsApp" data-p="+375 29 000-00-00" aria-pressed="false">WhatsApp</button>
                <button class="fchip" type="button" data-c="звонок" data-l="Телефон" data-p="+375 29 000-00-00" aria-pressed="false">Звонок</button>
              </div></div>
            <div class="field full rv" id="rvContact"><input id="f-contact" placeholder="@username"><label for="f-contact" id="lc">Ник в Telegram</label></div>
            <div class="field rv rvLast"><select id="f-fmt"><option>Конференция</option><option>Мастер-класс</option><option>Съёмка</option><option>Шоурум или pop-up</option><option>Фуршет или праздник</option><option>Офис на месяц</option><option>Другое</option></select><label for="f-fmt">Формат</label></div>
            <div class="field rv rvLast"><input id="f-guests" inputmode="numeric" value="40"><label for="f-guests">Гостей</label></div>
          </div>
          <div class="total rv rvLast">
            <span class="legal">Нажимая кнопку, вы соглашаетесь с <a href="<?php echo esc_url(arka_url('politika')); ?>">политикой обработки данных</a>.</span>
            <button class="btn btn-filled" type="submit"><span class="msi">send</span>Отправить заявку</button>
          </div>
        </form>
        <div class="step-body ok" id="ok" hidden>
          <span class="msi">check_circle</span>
          <h3 class="t-title">Дата за вами на 24 часа</h3>
          <p class="t-small" id="okTx" style="margin:0"><?php echo esc_html(arka_opt('manager')); ?> ответит в Telegram в течение 15 минут.</p>
        </div>
      </div>
    </div>
  </div>
</section>
<section class="w sec" id="formats-s" aria-labelledby="formats-h">
  <div class="car-head">
    <div class="head">
      <h2 class="h-sec" id="formats-h">Под что берут зал</h2>
    </div>
    <div class="car-nav">
      <button class="icon-btn" type="button" data-dir="-1" aria-label="Предыдущий формат"><span class="msi">arrow_back</span></button>
      <span class="car-count" id="cnt">1 / 5</span>
      <button class="icon-btn" type="button" data-dir="1" aria-label="Следующий формат"><span class="msi">arrow_forward</span></button>
    </div>
  </div>
  <div class="track" id="track" tabindex="0" aria-label="Форматы, листайте вбок">
    <a class="card" href="<?php echo esc_url(arka_url('formaty')); ?>#conf"><div class="ph"><img src="<?php echo esc_url(arka_asset('ph-conf.jpg')); ?>" alt="Зал с рядами стульев для конференции" loading="lazy" width="900" height="507" decoding="async"></div>
      <div class="meta"><div><h3 class="t-title">Конференции и мастер-классы</h3><span class="t-small">До 100 мест театром или 40 за столами</span></div><span class="price">от 90 BYN/ч</span></div></a>
    <a class="card" href="<?php echo esc_url(arka_url('formaty')); ?>#shoot"><div class="ph"><img src="<?php echo esc_url(arka_asset('ph-shoot.jpg')); ?>" alt="Съёмка у арочного окна" loading="lazy" width="507" height="900" decoding="async"></div>
      <div class="meta"><div><h3 class="t-title">Фото- и видеосъёмки</h3><span class="t-small">Свет из арок, Библиотека в кадре</span></div><span class="price">от 90 BYN/ч</span></div></a>
    <a class="card" href="<?php echo esc_url(arka_url('formaty')); ?>#show"><div class="ph"><img src="<?php echo esc_url(arka_asset('ph-show.jpg')); ?>" alt="Вешалки с одеждой в шоуруме" loading="lazy" width="507" height="900" decoding="async"></div>
      <div class="meta"><div><h3 class="t-title">Шоурумы и выставки</h3><span class="t-small">Pop-up и показы на 1–7 дней</span></div><span class="price">от 690 BYN/д</span></div></a>
    
    <a class="card" href="<?php echo esc_url(arka_url('formaty')); ?>#office"><div class="ph"><img src="<?php echo esc_url(arka_asset('ph-office.jpg')); ?>" alt="Рабочие места в светлом зале" loading="lazy" width="900" height="507" decoding="async"></div>
      <div class="meta"><div><h3 class="t-title">Офис на месяц</h3><span class="t-small">Команда до 20 человек, свои ключи</span></div><span class="price">3 900 BYN/мес</span></div></a>
    <a class="card" href="<?php echo esc_url(arka_url('formaty')); ?>#party"><div class="ph"><img src="<?php echo esc_url(arka_asset('ph-party.jpg')); ?>" alt="Фуршет на закате у окна" loading="lazy" width="900" height="678" decoding="async"></div>
      <div class="meta"><div><h3 class="t-title">Фуршеты и праздники</h3><span class="t-small">Корпоративы и вечеринки до 23:00</span></div><span class="price">от 120 BYN/ч</span></div></a>
  </div>
  <div class="progress" aria-hidden="true"><i id="bar"></i></div>
</section>
<section class="w sec" id="prices-s" aria-labelledby="prices-h">
  <div class="head">
    <h2 class="h-sec" id="prices-h">Сколько стоит</h2>
  </div>
  <div class="tiers">
    <div class="tier"><h3 class="t-title">Час</h3><span class="p">90 <small>BYN</small></span><span class="t-small">будни до 17:00, минимум 2 часа</span>
      <ul><li>Проектор, экран, звук</li><li>Wi-Fi 500 Мбит/с</li></ul></div>
    <div class="tier hi"><h3 class="t-title">Полдня</h3><span class="p">390 <small>BYN</small></span><span class="t-small">5 часов подряд, чаще всего берут</span>
      <ul><li>Всё из тарифа «Час»</li><li>Час на монтаж бесплатно</li></ul></div>
    <div class="tier"><h3 class="t-title">День</h3><span class="p">690 <small>BYN</small></span><span class="t-small">с 9:00 до 19:00</span>
      <ul><li>Монтаж накануне вечером</li><li>Хранение реквизита 3 дня</li></ul></div>
  </div>
  <p class="t-small note">Вечер и выходные 120 BYN в час. Кофе-брейк от 12 BYN за гостя.</p>
</section>
<section class="w sec" id="model-s" aria-labelledby="model-h">
  <div class="head"><h2 class="h-sec" id="model-h">Зал в 3D до визита</h2></div>
  <div class="model-sheet">
    <figure class="m-plan"><svg viewBox="0 0 600 440" role="img" aria-label="План зала 14200 на 8700 мм, рассадка театром на 80 мест">
        <g fill="none" stroke="#23272B">
          <path d="M45 60H563V373H45Z" stroke-width="7"/>
          <path d="M100 60H244M380 60H524" stroke="var(--kalka)" stroke-width="9"/>
          <path d="M100 56H244M100 64H244M380 56H524M380 64H524" stroke-width="1.2"/>
          <path d="M100 52A72 22 0 0 1 244 52M380 52A72 22 0 0 1 524 52" stroke-width=".8" stroke-dasharray="3 3"/>
          <path d="M500 373H540" stroke="var(--kalka)" stroke-width="9"/>
          <path d="M500 373A40 40 0 0 0 540 333M500 373V333" stroke-width="1"/>
          <rect x="272" y="170" width="16" height="16" fill="#23272B"/><rect x="272" y="262" width="16" height="16" fill="#23272B"/>
          <path d="M548 150V290" stroke-width="3"/>
        </g>
        <g fill="#213641"><rect x="90" y="100" width="13" height="11"/><rect x="90" y="130" width="13" height="11"/><rect x="90" y="160" width="13" height="11"/><rect x="90" y="190" width="13" height="11"/><rect x="90" y="220" width="13" height="11"/><rect x="90" y="250" width="13" height="11"/><rect x="90" y="280" width="13" height="11"/><rect x="90" y="310" width="13" height="11"/><rect x="128" y="100" width="13" height="11"/><rect x="128" y="130" width="13" height="11"/><rect x="128" y="160" width="13" height="11"/><rect x="128" y="190" width="13" height="11"/><rect x="128" y="220" width="13" height="11"/><rect x="128" y="250" width="13" height="11"/><rect x="128" y="280" width="13" height="11"/><rect x="128" y="310" width="13" height="11"/><rect x="166" y="100" width="13" height="11"/><rect x="166" y="130" width="13" height="11"/><rect x="166" y="160" width="13" height="11"/><rect x="166" y="190" width="13" height="11"/><rect x="166" y="220" width="13" height="11"/><rect x="166" y="250" width="13" height="11"/><rect x="166" y="280" width="13" height="11"/><rect x="166" y="310" width="13" height="11"/><rect x="204" y="100" width="13" height="11"/><rect x="204" y="130" width="13" height="11"/><rect x="204" y="160" width="13" height="11"/><rect x="204" y="190" width="13" height="11"/><rect x="204" y="220" width="13" height="11"/><rect x="204" y="250" width="13" height="11"/><rect x="204" y="280" width="13" height="11"/><rect x="204" y="310" width="13" height="11"/><rect x="242" y="100" width="13" height="11"/><rect x="242" y="130" width="13" height="11"/><rect x="242" y="160" width="13" height="11"/><rect x="242" y="190" width="13" height="11"/><rect x="242" y="220" width="13" height="11"/><rect x="242" y="250" width="13" height="11"/><rect x="242" y="280" width="13" height="11"/><rect x="242" y="310" width="13" height="11"/><rect x="304" y="100" width="13" height="11"/><rect x="304" y="130" width="13" height="11"/><rect x="304" y="160" width="13" height="11"/><rect x="304" y="190" width="13" height="11"/><rect x="304" y="220" width="13" height="11"/><rect x="304" y="250" width="13" height="11"/><rect x="304" y="280" width="13" height="11"/><rect x="304" y="310" width="13" height="11"/><rect x="342" y="100" width="13" height="11"/><rect x="342" y="130" width="13" height="11"/><rect x="342" y="160" width="13" height="11"/><rect x="342" y="190" width="13" height="11"/><rect x="342" y="220" width="13" height="11"/><rect x="342" y="250" width="13" height="11"/><rect x="342" y="280" width="13" height="11"/><rect x="342" y="310" width="13" height="11"/><rect x="380" y="100" width="13" height="11"/><rect x="380" y="130" width="13" height="11"/><rect x="380" y="160" width="13" height="11"/><rect x="380" y="190" width="13" height="11"/><rect x="380" y="220" width="13" height="11"/><rect x="380" y="250" width="13" height="11"/><rect x="380" y="280" width="13" height="11"/><rect x="380" y="310" width="13" height="11"/><rect x="418" y="100" width="13" height="11"/><rect x="418" y="130" width="13" height="11"/><rect x="418" y="160" width="13" height="11"/><rect x="418" y="190" width="13" height="11"/><rect x="418" y="220" width="13" height="11"/><rect x="418" y="250" width="13" height="11"/><rect x="418" y="280" width="13" height="11"/><rect x="418" y="310" width="13" height="11"/><rect x="456" y="100" width="13" height="11"/><rect x="456" y="130" width="13" height="11"/><rect x="456" y="160" width="13" height="11"/><rect x="456" y="190" width="13" height="11"/><rect x="456" y="220" width="13" height="11"/><rect x="456" y="250" width="13" height="11"/><rect x="456" y="280" width="13" height="11"/><rect x="456" y="310" width="13" height="11"/></g>
        <g stroke="#213641" stroke-width="1" fill="none"><path d="M45 400H563M45 392v16M563 392v16M22 60V373M14 60h16M14 373h16M100 38H244M100 32v12M244 32v12"/></g>
        <g fill="#213641" font-family="Roboto, system-ui, sans-serif" font-size="13">
          <text x="304" y="420" text-anchor="middle">14200</text>
          <text x="12" y="216" text-anchor="middle" transform="rotate(-90 12 216)">8700</text>
          <text x="172" y="28" text-anchor="middle" font-size="11">окно 4000</text>
          <text x="452" y="28" text-anchor="middle" font-size="11">окно 4000</text>
          <text x="540" y="220" text-anchor="end" font-size="11" fill="#5E646A" transform="rotate(-90 540 220)">экран</text>
          <text x="520" y="362" text-anchor="end" font-size="11" fill="#5E646A">вход</text>
        </g>
      </svg><figcaption><span>План зала, М 1:100</span><span>рассадка «театр», 80 мест</span></figcaption></figure>
    <figure class="m-render"><a href="<?php echo esc_url(arka_asset('3d.html')); ?>"><img src="<?php echo esc_url(arka_asset('flight-last.jpg')); ?>" alt="3D-модель зала: арочные окна, паркет ёлочкой, объёмные цифры 123 у окна" loading="lazy" width="1280" height="720" decoding="async"></a><figcaption><span>3D-модель, построена по замерам</span><span>14,2 × 8,7 м, потолок 4,5 м</span></figcaption></figure>
    <div class="m-text"><p>Пройдитесь по залу, посмотрите вид из окон и прикиньте расстановку. Модель открывается в браузере, ничего ставить не нужно.</p><a class="btn btn-filled" href="<?php echo esc_url(arka_asset('3d.html')); ?>">Войти в 3D</a></div>
  </div>
</section>
<section class="w sec" id="reviews-s" aria-labelledby="reviews-h">
  <div class="head"><h2 class="h-sec" id="reviews-h">Что говорят после мероприятий</h2></div>
  <div class="revs">
    <figure class="rev"><span class="ev">Мастер-класс, 40 гостей</span><blockquote>Боялись, что к вечеру будет темно. До шести работали вообще без верхнего света, фотограф ни разу не достал вспышку.</blockquote><figcaption><b>Ольга, HR</b><span>октябрь 2026</span></figcaption></figure>
    <figure class="rev"><span class="ev">Съёмка каталога, 4 часа</span><blockquote>Сняли 60 образов у одного окна. Библиотека в кадре сработала лучше любого фона, ретушёр почти ничего не правил.</blockquote><figcaption><b>Дмитрий, фотограф</b><span>сентябрь 2026</span></figcaption></figure>
    <figure class="rev"><span class="ev">Митап, 80 гостей</span><blockquote>Звук и проектор были готовы к нашему приходу. Монтаж заняли накануне вечером бесплатно, утром просто открыли двери.</blockquote><figcaption><b>Кирилл, организатор</b><span>август 2026</span></figcaption></figure>
  </div>
  <p class="sum">140 мероприятий за первый год. В демо-версии сайта отзывы приведены для примера.</p>
</section>
<section class="w sec desk-only" id="lead-s" aria-labelledby="lead-h">
  <div class="lead">
    <div class="lead-in">
      <h2 class="h-sec" id="lead-h">Расскажите о мероприятии</h2>
      <p class="t-small" style="margin:0;font-size:16px;line-height:24px">Ответим в удобном мессенджере в течение 15 минут.</p>
      <ol><li>Уточним формат и время</li><li>Пришлём смету и схему расстановки</li><li>Покажем зал вживую или в 3D</li></ol>
    </div>
    <form class="lead-f" id="leadF">
      <input id="hp2" name="website" tabindex="-1" autocomplete="off" aria-hidden="true" style="position:absolute;left:-9999px">
      <div class="pickbar"><div><small>Вы выбрали</small><b id="pick2">Дата не выбрана</b></div><a class="btn btn-text" href="#book-s">Изменить</a></div>
      <div class="fields">
        <div class="field"><input id="l-name" autocomplete="name" placeholder=" "><label for="l-name">Имя</label></div>
        <div class="field"><select id="l-fmt"><option>Конференция</option><option>Мастер-класс</option><option>Съёмка</option><option>Шоурум или pop-up</option><option>Фуршет или праздник</option><option>Офис на месяц</option><option>Другое</option></select><label for="l-fmt">Формат</label></div>
        <div class="grp field full" style="gap:12px"><span class="grp-l">Как с вами связаться</span>
          <div class="chips" id="chan2">
            <button class="fchip" type="button" data-c="1" data-l="Ник в Telegram" data-p="@username" aria-pressed="true">Telegram</button>
            <button class="fchip" type="button" data-c="1" data-l="Номер WhatsApp" data-p="+375 29 000-00-00" aria-pressed="false">WhatsApp</button>
            <button class="fchip" type="button" data-c="1" data-l="Номер Viber" data-p="+375 29 000-00-00" aria-pressed="false">Viber</button>
            <button class="fchip" type="button" data-c="1" data-l="Телефон" data-p="+375 29 000-00-00" aria-pressed="false">Звонок</button>
            <button class="fchip" type="button" data-c="1" data-l="E-mail" data-p="name@company.by" aria-pressed="false">E-mail</button>
          </div></div>
        <div class="field full"><input id="l-contact" placeholder="@username"><label for="l-contact" id="l-cl">Ник в Telegram</label></div>
        <div class="field"><input id="l-guests" inputmode="numeric" value="40"><label for="l-guests">Гостей</label></div>
        <div class="field"><input id="l-msg" placeholder="Техника, кофе-брейк"><label for="l-msg">Комментарий</label></div>
      </div>
      <div class="total"><span class="legal">Нажимая кнопку, вы соглашаетесь с <a href="<?php echo esc_url(arka_url('politika')); ?>">политикой обработки данных</a>.</span><button class="btn btn-filled" type="submit" id="lsend"><span class="msi">send</span>Отправить заявку</button></div>
    </form>
  </div>
</section>
<section class="w sec" id="faq-s" aria-labelledby="faq-h">
  <div class="faq">
    <div class="faq-side">
      <h2 class="h-sec" id="faq-h">Частые вопросы</h2>
      <div class="faq-ark hov"><?php arka_mascot('lost'); ?><p><b>Аркадий, управляющий</b><span>Не нашли ответ? Спросите Анну в Telegram, она отвечает с 9:00 до 21:00. А я пока подержу дверь.</span></p></div>
    </div>
    <div>
      <?php arka_faq_list(7); ?>

    </div>
  </div>
</section>
<section class="w sec" id="contact-s" aria-labelledby="contact-h">
  <div class="contact">
    <div>
      <div class="head"><h2 class="h-sec" id="contact-h">Мстиславца, 10, второй этаж</h2></div>
      <ul class="list">
        <li><svg class="tg" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M21.4 4.2 2.9 11.3c-1.3.5-1.3 1.2-.2 1.5l4.7 1.5 1.8 5.6c.2.6.1.9.8.9.5 0 .7-.2 1-.5l2.3-2.2 4.8 3.5c.9.5 1.5.2 1.7-.8l3.1-14.7c.3-1.3-.5-1.9-1.5-1.5zM8.6 14.1l9.6-6.1c.5-.3.9-.1.5.2l-8.2 7.4-.3 3.4z"/></svg><div><b>Telegram <?php echo esc_html('@' . arka_opt('telegram')); ?></b><span><?php echo esc_html(arka_opt('manager')); ?>, менеджер, отвечает за 15 минут</span></div></li>
        <li><span class="msi">call</span><div><b><?php echo esc_html(arka_opt('phone')); ?></b><span><?php echo esc_html(arka_opt('phone_note')); ?></span></div></li>
        <li><span class="msi">mail</span><div><b><?php echo esc_html(arka_opt('email')); ?></b><span>Счета и документы для юрлиц</span></div></li>
        <li><span class="msi">directions_subway</span><div><b>Метро «Восток», 7 минут</b><span>Вход со двора, парковка на 30 мест</span></div></li>
      </ul>
    </div>
    <div class="ph"><img src="<?php echo esc_url(arka_asset('ph-ext.jpg')); ?>" alt="Вид из окна зала на Национальную библиотеку" loading="lazy" width="900" height="507" decoding="async"></div>
  </div>
</section>

<?php get_footer();
