
</main>

<footer class="foot"><div class="w foot-grid">
  <div><b>АРКА 123</b><span><?php echo esc_html(arka_opt('address')); ?></span><span><a href="<?php echo esc_attr(arka_tel()); ?>"><?php echo esc_html(arka_opt('phone')); ?></a> · <?php echo (int) arka_opt('open'); ?>:00–<?php echo (int) arka_opt('close'); ?>:00</span><span><a href="mailto:<?php echo esc_attr(arka_opt('email')); ?>"><?php echo esc_html(arka_opt('email')); ?></a></span></div>
  <nav class="foot-nav" aria-label="Страницы"><a href="<?php echo esc_url(home_url('/')); ?>">Главная</a><?php foreach (arka_nav_items() as $it) printf('<a href="%s">%s</a>', esc_url($it['url']), esc_html($it['title'])); ?><a href="<?php echo esc_url(home_url('/')); ?>#book-s">Бронь</a><a href="<?php echo esc_url(arka_asset('3d.html')); ?>">3D-режим</a></nav>
  <div><span><?php echo esc_html(arka_opt('company')); ?></span><span>УНП <?php echo esc_html(arka_opt('unp')); ?></span><span><a href="<?php echo esc_url(arka_url('politika')); ?>">Политика обработки данных</a></span></div>
  <div class="foot-bottom"><span>© <?php echo esc_html(wp_date('Y')); ?> АРКА 123</span><span>Зал с арочными окнами напротив Национальной библиотеки</span></div>
</div></footer>
</div>
<?php wp_footer(); ?>
</body>
</html>
