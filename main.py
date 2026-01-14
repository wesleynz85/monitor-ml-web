import flet as ft
from datetime import datetime
import database
import scraper
import scheduler
import config

# --- Tentativa de Importação Segura para Gráficos ---
try:
    # Tenta importar diretamente da raiz (versões padrão)
    from flet import LineChartDataPoint
except ImportError:
    # Se falhar, define como None para ativar o modo "Lista de Texto"
    LineChartDataPoint = None

def main(page: ft.Page):
    page.title = "Cockpit Monitor ML 2.0"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    
    # --- Estado ---
    monitor_ativo = False
    
    def log_sistema(msg):
        """Callback para logs"""
        if txt_log: 
            txt_log.value += f"[{datetime.now().strftime('%H:%M')}] {msg}\n"
            page.update()

    service = scheduler.MonitorService(log_sistema)

    # --- Funções da Lógica ---

    def atualizar_unico_produto(produto):
        """Força a atualização de um único produto imediatamente"""
        url = produto['url']
        nome = produto['nome']
        
        page.snack_bar = ft.SnackBar(ft.Text(f"Verificando {nome[:20]}..."), bgcolor="blue")
        page.snack_bar.open = True
        page.update()
        
        dados_novos, erro = scraper.extrair_dados_url(url)
        
        if dados_novos:
            novo_preco = dados_novos['preco']
            old_price = produto['preco_atual']
            
            database.atualizar_preco_produto(produto['id'], novo_preco)
            
            diff = novo_preco - old_price
            if diff != 0:
                log_sistema(f"MANUAL: {nome[:10]} variou R$ {diff:.2f}")
                cor_snack = "green" if diff < 0 else "red"
                texto_snack = f"Preço mudou: R$ {old_price:.2f} -> R$ {novo_preco:.2f}"
            else:
                log_sistema(f"MANUAL: {nome[:10]} verificado (sem alteração).")
                cor_snack = "grey"
                texto_snack = f"Preço confirmado: R$ {novo_preco:.2f}"
                
            page.snack_bar = ft.SnackBar(ft.Text(texto_snack), bgcolor=cor_snack)
            atualizar_lista_produtos() 
        else:
            log_sistema(f"ERRO MANUAL: {nome[:10]} - {erro}")
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao ler site: {erro}"), bgcolor="red")
            
        page.snack_bar.open = True
        page.update()
    
    def atualizar_lista_produtos(e=None):
        """Recarrega a tabela de dados"""
        termo = filtro_nome.value.lower()
        dados = database.carregar_dados()
        
        tabela.rows.clear()
        
        for p in dados:
            if termo and termo not in p['nome'].lower():
                continue
            
            p_atual = f"R$ {p['preco_atual']:.2f}"
            dt_check = datetime.fromisoformat(p['ultimo_check']).strftime('%d/%m %H:%M')
            
            historico = p.get('historico', [])
            if len(historico) > 1:
                p_anterior = historico[-2]['preco']
                diff = p['preco_atual'] - p_anterior
                if diff < 0:
                    str_var = f"⬇️ {diff:.2f}"
                    color_var = "green"
                elif diff > 0:
                    str_var = f"⬆️ +{diff:.2f}"
                    color_var = "red"
                else:
                    str_var = "-"
                    color_var = "white"
            else:
                str_var = "Novo"
                color_var = "blue"

            row = ft.DataRow(
                cells=[
                    ft.DataCell(ft.Switch(value=p['ativo'], on_change=lambda e, id=p['id']: toggle_status(id, e))),
                    ft.DataCell(ft.Text(p['nome'], width=200, no_wrap=True, tooltip=p['nome'])),
                    ft.DataCell(ft.Text(p_atual, weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(str_var, color=color_var)),
                    ft.DataCell(ft.Text(dt_check)),
                    ft.DataCell(
                        ft.Row([
                            ft.IconButton(ft.Icons.REFRESH, tooltip="Atualizar Agora", icon_color="blue", on_click=lambda e, x=p: atualizar_unico_produto(x)),
                            ft.IconButton(ft.Icons.SHOW_CHART, tooltip="Ver Histórico", on_click=lambda e, x=p: abrir_historico(x)),
                            ft.IconButton(ft.Icons.DELETE, icon_color="red", tooltip="Remover", on_click=lambda e, id=p['id']: deletar_prod(id)),
                            # CORREÇÃO 1: Usando propriedade 'url' direta para evitar erro async/await
                            ft.IconButton(ft.Icons.LINK, tooltip="Abrir Link", url=p['url'])
                        ], spacing=0)
                    ),
                ]
            )
            tabela.rows.append(row)
        page.update()

    def adicionar_click(e):
        url = txt_url.value
        if not url: return
        
        btn_add.disabled = True
        txt_url.disabled = True
        page.update()
        
        page.snack_bar = ft.SnackBar(ft.Text(f"Buscando dados... aguarde."))
        page.snack_bar.open = True
        page.update()
        
        dados, erro = scraper.extrair_dados_url(url)
        
        if dados:
            ok, msg = database.adicionar_produto(url, dados['nome'], dados['preco'])
            if ok:
                txt_url.value = ""
                atualizar_lista_produtos()
                page.snack_bar = ft.SnackBar(ft.Text("Produto Adicionado!"), bgcolor="green")
            else:
                page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor="red")
        else:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro: {erro}"), bgcolor="red")
            
        page.snack_bar.open = True
        btn_add.disabled = False
        txt_url.disabled = False
        page.update()

    def toggle_status(id_prod, e):
        database.toggle_ativo(id_prod, e.control.value)
        log_sistema(f"Status do ID {id_prod} alterado.")

    def deletar_prod(id_prod):
        database.remover_produto(id_prod)
        atualizar_lista_produtos()

    def toggle_monitor(e):
        nonlocal monitor_ativo
        monitor_ativo = not monitor_ativo
        if monitor_ativo:
            btn_monitor.text = "PARAR MONITOR"
            btn_monitor.bgcolor = "red400"
            btn_monitor.icon = ft.Icons.STOP
            service.start()
        else:
            btn_monitor.text = "INICIAR MONITOR"
            btn_monitor.bgcolor = "green400"
            btn_monitor.icon = ft.Icons.PLAY_ARROW
            service.stop()
        page.update()

    def abrir_modal_cookie(e):
        dlg_cookie.open = True
        page.update()
        
    def salvar_cookie_click(e):
        config.salvar_cookie(txt_cookie_input.value)
        dlg_cookie.open = False
        page.snack_bar = ft.SnackBar(ft.Text("Cookie Salvo!"))
        page.snack_bar.open = True
        page.update()

    def abrir_historico(produto):
        """Abre o histórico. Se tiver gráfico, mostra gráfico. Se não, mostra lista."""
        hist = produto.get('historico', [])
        
        if not hist:
            page.snack_bar = ft.SnackBar(ft.Text("Sem histórico suficiente."), bgcolor="grey")
            page.snack_bar.open = True
            page.update()
            return
            
        conteudo_modal = None
        
        # --- OPÇÃO 1: Tenta Gerar Gráfico ---
        if LineChartDataPoint:
            try:
                data_points = []
                precos = [h['preco'] for h in hist]
                min_p, max_p = min(precos), max(precos)
                margem = (max_p - min_p) * 0.1 if max_p != min_p else max_p * 0.1
                
                for i, h in enumerate(hist):
                    ponto = LineChartDataPoint(
                        x=i, 
                        y=h['preco'],
                        tooltip=f"R$ {h['preco']:.2f}\n{datetime.fromisoformat(h['data']).strftime('%d/%m %H:%M')}"
                    )
                    data_points.append(ponto)

                chart = ft.LineChart(
                    data_series=[
                        ft.LineChartData(
                            data_points=data_points,
                            stroke_width=3,
                            color="cyan",
                            curved=True,
                            stroke_cap_round=True,
                        )
                    ],
                    border=ft.Border.all(1, "white10"),
                    left_axis=ft.ChartAxis(labels_size=40, title=ft.Text("Preço"), title_size=20),
                    bottom_axis=ft.ChartAxis(labels_size=20, title=ft.Text("Check"), title_size=20),
                    min_y=max(0, min_p - margem),
                    max_y=max_p + margem,
                    tooltip_bgcolor=ft.colors.with_opacity(0.8, "grey900"),
                )
                conteudo_modal = ft.Container(chart, padding=20, height=300, width=500)
            except Exception as e:
                print(f"Falha ao gerar gráfico: {e}")
                conteudo_modal = None # Fallback para lista
        
        # --- OPÇÃO 2: Lista de Texto (Fallback) ---
        if conteudo_modal is None:
            lista_hist = ft.ListView(expand=1, spacing=10, padding=20, height=300)
            # Inverte para mostrar o mais recente no topo
            for h in reversed(hist):
                dt = datetime.fromisoformat(h['data']).strftime('%d/%m/%Y às %H:%M')
                pr = f"R$ {h['preco']:.2f}"
                lista_hist.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(dt, color="grey"),
                            ft.Text(pr, weight=ft.FontWeight.BOLD, color="white")
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        # CORREÇÃO 2: Border.only (Maiúsculo)
                        border=ft.Border.only(bottom=ft.BorderSide(1, "white10"))
                    )
                )
            conteudo_modal = ft.Column([
                ft.Text("Modo Lista (Gráfico indisponível)", size=12, color="red"),
                ft.Container(lista_hist, height=300, width=400)
            ])

        dlg_grafico.content = conteudo_modal
        dlg_grafico.title = ft.Text(f"Histórico: {produto['nome'][:30]}...")
        dlg_grafico.open = True
        page.update()

    # --- Elementos da UI ---
    
    txt_url = ft.TextField(hint_text="Cole o Link do Produto aqui...", expand=True)
    btn_add = ft.FilledButton("Adicionar", icon=ft.Icons.ADD, on_click=adicionar_click)
    btn_cookie = ft.IconButton(ft.Icons.COOKIE, tooltip="Configurar Cookie", on_click=abrir_modal_cookie)
    
    header = ft.Row([txt_url, btn_add, btn_cookie], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    
    btn_monitor = ft.FilledButton("INICIAR MONITOR", icon=ft.Icons.PLAY_ARROW, style=ft.ButtonStyle(bgcolor="green400"), on_click=toggle_monitor, height=50)
    filtro_nome = ft.TextField(label="Filtrar nome...", width=200, on_change=atualizar_lista_produtos, prefix_icon=ft.Icons.SEARCH)
    
    controls = ft.Row([btn_monitor, filtro_nome], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    
    tabela = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Ativo")),
            ft.DataColumn(ft.Text("Produto")),
            ft.DataColumn(ft.Text("Preço Atual")),
            ft.DataColumn(ft.Text("Var.")),
            ft.DataColumn(ft.Text("Últ. Check")),
            ft.DataColumn(ft.Text("Ações")),
        ],
        rows=[],
        expand=True,
        border=ft.Border.all(1, "white10"),
        vertical_lines=ft.border.BorderSide(1, "white10"),
    )
    
    txt_log = ft.Text(value="Sistema Inicializado...\n", font_family="Consolas", size=12, color="green300")
    log_container = ft.Container(
        content=ft.Column([txt_log], scroll=ft.ScrollMode.ALWAYS),
        height=150,
        bgcolor="black54",
        padding=10,
        border_radius=5
    )

    txt_cookie_input = ft.TextField(label="Cole o Cookie aqui", multiline=True)
    dlg_cookie = ft.AlertDialog(
        title=ft.Text("Configurar Cookie ML"),
        content=txt_cookie_input,
        actions=[ft.TextButton("Salvar", on_click=salvar_cookie_click)]
    )
    
    dlg_grafico = ft.AlertDialog(
        title=ft.Text("Gráfico"),
        content=ft.Container()
    )
    page.dialog = dlg_grafico
    page.overlay.append(dlg_cookie)
    page.overlay.append(dlg_grafico)

    page.add(
        ft.Text("Monitor de Preços ML 2.0", size=30, weight=ft.FontWeight.BOLD),
        header,
        ft.Divider(),
        controls,
        ft.Divider(),
        ft.Container(tabela, expand=True, border_radius=10),
        ft.Text("Logs do Sistema:", weight=ft.FontWeight.BOLD),
        log_container
    )
    
    headers = config.get_headers()
    if "Cookie" in headers:
        txt_cookie_input.value = headers["Cookie"]
    atualizar_lista_produtos()

if __name__ == "__main__":
    import os
    # Pega a porta do servidor ou usa 8000 se for local
    porta = int(os.getenv("PORT", 8000))
    
    # Inicia como Site (WEB_BROWSER) na porta correta
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=porta)