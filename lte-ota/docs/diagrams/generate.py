#!/usr/bin/env python3
"""Generate editable SVG recipe diagrams using Python 3 standard library only."""
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parent
W, H = 1800, 900
INK, BLUE, GREEN, ORANGE = '#162b45', '#1263a0', '#087d70', '#aa530b'

class Diagram:
    def __init__(self, title, subtitle):
        self.parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(subtitle)}</desc>
<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="{BLUE}"/></marker></defs>
<rect width="1800" height="900" fill="#fff"/>
<g font-family="Arial, 'Hiragino Kaku Gothic ProN', 'Noto Sans CJK JP', sans-serif" fill="{INK}">''']
        self.text(40, 52, [title], 34, True)
        self.text(40, 91, [subtitle], 22)
    def text(self,x,y,lines,size=24,bold=False,color=INK):
        for i,line in enumerate(lines):
            self.parts.append(f'<text x="{x}" y="{y+i*(size+10)}" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{escape(line)}</text>')
    def box(self,x,y,w,h,title,lines,fill='#f2f7fc',stroke='#bdcede',size=23):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        self.text(x+18,y+36,[title],24,True)
        self.text(x+18,y+76,lines,size)
    def region(self,x,y,w,h,title):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="#fafcfe" stroke="#aec3d5" stroke-width="2"/>')
        self.text(x+20,y+38,[title],26,True)
    def arrow(self,points,both=False,dashed=False):
        path='M '+' L '.join(f'{x} {y}' for x,y in points)
        self.parts.append(f'<path d="{path}" fill="none" stroke="{BLUE}" stroke-width="3" marker-end="url(#arrow)"'+(' marker-start="url(#arrow)"' if both else '')+(' stroke-dasharray="8 6"' if dashed else '')+'/>')
    def save(self,name):
        (ROOT/name).write_text('\n'.join(self.parts+['</g></svg>']),encoding='utf-8')

d=Diagram('LTE OTA の全体構成', '左から右へ：PCで作る → SORACOMへ置く → 端末が取得・検証して更新する')
d.region(40,125,330,635,'1  開発者PC')
d.region(430,125,410,635,'2  SORACOM')
d.region(900,125,860,635,'3  Wio BG770A HW v1.0')
d.box(60,185,290,150,'ビルド・署名',['秘密鍵はPC側に保管','公開鍵はアプリへ組込'])
d.box(60,375,290,140,'manifest.json',['版・URL・ハッシュ','署名を含む更新情報'])
d.box(60,575,290,125,'firmware.bin',['ZIPから抽出したアプリ'])
d.arrow([(205,335),(205,375)])
d.arrow([(76,335),(47,335),(47,638),(60,638)])
d.box(450,375,370,140,'Metadata のユーザーデータ',['SIMグループにJSONを設定','GET /v1/userdata'])
d.box(450,575,370,125,'Harvest Files',['firmware.bin を保存','GET manifestのURL'])
d.arrow([(350,445),(450,445)])
d.arrow([(350,638),(450,638)])
d.text(458,225,['更新情報とアプリは別の場所。','manifestのJSON内容を設定し、','バイナリだけをアップロード。'],23)
d.box(920,375,210,230,'BG770A',['LTE・HTTP','端末からGET','firmwareは','UFS一時ファイル','を経由'],size=22)
d.arrow([(820,445),(920,445)],both=True)
d.arrow([(820,638),(870,638),(870,550),(920,550)],both=True)
d.text(850,408,['①'],22,True)
d.text(850,608,['②'],22,True)
d.region(1160,185,580,545,'nRF52840 / 内部Flash')
d.box(1180,250,245,150,'Bank 0：実行アプリ',['WioOtaAgent','公開鍵で署名検証'],size=22)
d.box(1460,250,260,150,'Bank 1：次のアプリ',['順次書込み・読戻し','全量受信後に照合'],size=22)
d.arrow([(1130,410),(1150,410),(1150,325),(1180,325)],both=True)
d.text(920,295,['ATコマンド / データ'],20)
d.arrow([(1425,325),(1460,325)])
d.box(1180,460,245,120,'InternalFS',['最高適用版を保存'],size=22)
d.arrow([(1300,400),(1300,460)],both=True)
d.box(1460,460,260,120,'bootloader settings',['検証後に適用登録'],size=22)
d.arrow([(1425,375),(1442,375),(1442,520),(1460,520)])
d.box(1180,620,540,90,'ブートローダー：再起動後にコピー',[],size=22)
d.text(1198,690,['Bank 1 → Bank 0 を確認して起動'],22)
d.arrow([(1590,580),(1590,620)],dashed=True)
d.arrow([(1720,360),(1732,360),(1732,665),(1720,665)])
d.text(40,808,['① manifest取得・署名検証 → ② 条件を満たす場合だけfirmware取得。秘密鍵はクラウド・端末へ置きません。'],24)
d.text(40,854,['凡例：実線＝データ・保存、双方向＝要求と応答、破線＝再起動後の参照。領域は容量比ではありません。'],22)
d.save('architecture.svg')

d=Diagram('LTE OTA の更新フロー', '各段を左から右へ読む：①〜④ 判定・取得 → ⑤〜⑧ 検証・反映（署名必須サンプル）')
xs=[40,480,920,1360]
steps=[
('① 起動・準備',['最高適用版を読み込む','現在の版を記録・LTE接続']),
('② 更新情報を取得',['Metadataからmanifest取得','形式・HW・URL・サイズ確認']),
('③ 署名と適用条件',['公開鍵で署名を検証','次に版・rollout・適用判断']),
('④ アプリを取得・格納',['GET応答確認 → Bank 1準備','UFS経由で書込み・読戻し','CRC16 / SHA-256を計算']),
('⑤ 全量を照合',['サイズ・CRC16・SHA-256','起動先情報（ベクタ）を確認']),
('⑥ 適用を登録',['BG770Aを停止','settingsに適用情報を登録','両方に成功したらリセット']),
('⑦ bootloaderで反映',['Bank 1 → Bank 0へコピー','アプリを確認して起動']),
('⑧ 起動後を確認',['新しい版・最高適用版を確認','同じmanifestで no update'])]
for i,(title,lines) in enumerate(steps):
    y=150 if i<4 else 510
    d.box(xs[i%4],y,400,185,title,lines,size=23)
    if i%4<3:d.arrow([(xs[i%4]+400,y+92),(xs[i%4]+440,y+92)])
d.text(40,132,['判定・取得'],24,True,color=BLUE)
d.text(40,492,['検証・反映'],24,True,color=GREEN)
# Explicit continuation travels around the row, without reversing the numbered reading order.
d.arrow([(1760,242),(1780,242),(1780,440),(20,440),(20,602),(40,602)])
d.text(700,426,['④ の受信完了後、⑤ へ'],22,True,color=BLUE)
fails=[
(40,350,400,['保存状態・LTE異常：開始しない']),
(480,350,840,['取得失敗・不正・旧版・同版・対象外：firmwareを取得しない']),
(1360,350,400,['転送・書込失敗：登録しない']),
(40,710,400,['検証失敗：適用登録しない']),
(480,710,400,['失敗：更新用リセットしない'])]
for x,y,w,lines in fails:
    d.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="48" rx="8" fill="#fff3e7"/>')
    d.text(x+12,y+31,lines,20,False,ORANGE)
d.text(920,741,['自動ロールバックなし / 版の記録は業務全体の正常判定ではない'],20,False,ORANGE)
d.text(40,811,['署名は取得前、全量ハッシュ照合は書込み後。失敗時、Bank 1に途中データが残る場合があります。'],24)
d.text(40,854,['settings書込み・コピー中の電源断からの復旧は保証していません。対応bootloaderとUSB復旧環境が前提です。'],22)
d.save('update-flow.svg')
