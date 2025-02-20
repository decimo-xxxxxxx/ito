
from os import environ
from discord import Intents, Client, Interaction
from discord.app_commands import CommandTree
import json
import random

# json の読み込み
# with 文はファイルを開いた後、その後の処理が終わった時点で自動的にファイルを閉じてくれる
# r=ファイルを読み込みモード 
with open('themes.json', 'r', encoding='utf-8') as f:
    config = json.load(f) # JSON のデータを Python のデータ型に自動変換
themes = config.get("themes", [])  # themes というキーが config 辞書に存在する場合はその値（リスト）を返


#Clientクラスの継承 
class MyClient(Client):
    # 戻り値なしで(-> None)クラスのインスタンスを初期化
    # アンダースコア2つで囲まれているメソッドは、「マジックメソッド」または「特殊メソッド」という
    # self は、インスタンスメソッドでクラスのインスタンス自身を指す引数の名前です。
    # これにより、クラス内でそのインスタンスの属性やメソッドにアクセスできるようになります。
    def __init__(self, intents: Intents) -> None:       
        super().__init__(intents=intents)
        self.tree = CommandTree(self)
        
    async def setup_hook(self) -> None:
        # コマンドを同期
        await self.tree.sync()
       
    async def on_ready(self):
    # 起動したらターミナルにログイン通知が表示される
         print(f"login: {self.user.name} [{self.user.id}]")
       
intents = Intents.default()
intents.message_content = True # メッセージの内容を取得でき
intents.members = True # サーバーのメンバー情報を取得できる
intents.voice_states = True # 誰がボイスチャンネルにいるかを取得できる
client = MyClient(intents=intents)

#デコレーター：関数にコードの中身を変更せずに処理の追加、変更出来る
#元の関数の前後に処理を追加することができます。
#
@client.tree.command(name="join",description="ボイスチャットに参加") 
async def join(interaction: Interaction):
    if interaction.user.voice: # コマンドが送信されたユーザーがボイスチャンネルに参加しているか確認
        channel = interaction.user.voice.channel  # ユーザーが参加しているボイスチャンネル
        # ボイスチャンネルに接続
        voice_client = await channel.connect()
        await interaction.response.send_message(f"{channel.name} に参加しました。")
    else:
        await interaction.response.send_message("ボイスチャンネルに参加して/joinを実行してください。")

@client.tree.command(name="start",description="ゲームを開始します") 
async def start(interaction: Interaction):
    # ボットがどのボイスチャンネルに接続しているか取得
    voice_client = interaction.guild.voice_client
    if voice_client is None or voice_client.channel is None:
        # ephemeral=True を指定すると、そのメッセージが送信者（コマンドを実行したユーザー）にしか見えなくなる
        await interaction.response.send_message("ボイスチャットに接続していません。まずは `/join` コマンドを実行してください。", ephemeral=True)
        return
   
       # 現在接続中のボイスチャンネルの参加者（ボット以外）を取得
       # voice_client.channel.members は そのチャンネルにいるすべてのメンバー（ユーザー & ボット） のリストを取得
       # if not member.bot の条件で、ボットではないメンバーのみをリストに格納(members.append(member))
    members = [member for member in voice_client.channel.members if not member.bot] # リスト内包表記（リストコンプリヘンション）
    if not members:
        await interaction.response.send_message("ボイスチャットに参加しているプレイヤーが見つかりません。", ephemeral=True)
        return
    
    # config のテーマリストからランダムにテーマを選ぶ
    if themes:
        chosen_theme = random.choice(themes) # 例えば themes = ["海", "宇宙", "未来"] の場合、 "海" や "宇宙" などがランダムに選ばれる。
    else:
        chosen_theme = "テーマを読み込めませんでした。参加者でテーマを考えてください。"
    
    # テーマをテキストチャンネル（コマンド実行先）に送信
    await interaction.channel.send(f"**テーマ：** {chosen_theme}")

    # 1～100 の数字デッキを作成してシャッフル
    deck = list(range(1, 101))
    random.shuffle(deck) # リスト deck の中の要素をランダムな順番に並び替える

    # 各参加者に対して、重複しない数字を DM で送信
    error_list = []
    for member in members:
        if not deck:
            # 万が一参加者が 100 人を超えた場合のフォールバック
            try:
                await member.send("申し訳ありません。ナンバーカードが不足しています。")
            except Exception as e:
                error_list.append(f"{member.name} への DM 送信に失敗しました: {e}")
        else:
            # 取り出した要素はリストから削除され、リストの長さも1つ減ります。
            card = deck.pop()
            try:
                await member.send(f"あなたのナンバーカードは **{card}** です。")
            except Exception as e:
                error_list.append(f"{member.name} への DM 送信に失敗しました: {e}")

    # 全員にDM送信完了後、テキストチャンネルに完了メッセージを送信
    await interaction.channel.send("ナンバーカードを配りました。")

    # DM送信に失敗した場合は、エラー内容もテキストチャンネルに出力（任意）
    if error_list:
        error_message = "\n".join(error_list)
        await interaction.channel.send(f"以下のユーザーへのDM送信に失敗しました:\n{error_message}")

    # ユーザーには処理完了の旨をエフェメラルメッセージでも通知
    await interaction.response.send_message("ゲーム開始処理が完了しました。", ephemeral=True)


# Botの起動とDiscordサーバーへの接続
client.run(environ.get("TOKEN"))
