# Blender MeshPort

**Blender MeshPort** は、[Blender公式MCPアドオン](https://projects.blender.org/lab/blender_mcp) の通信機能とFBXを利用して、MayaとBlenderの間でメッシュデータを双方向に転送するMaya用ツールです。

Maya標準の **`maya.cmds` GUI** からBlenderシーンのメッシュ一覧を確認し、必要なメッシュを選んで送受信できます。定型操作のたびにAIエージェントへ指示する必要はありません。

> **バージョン：** 1.0.0  
> **検証状況：** Python構文チェックとモックを使った単体テストは成功しています。Maya ↔ Blenderの実機での一連の転送については、正式な動作保証の前に確認が必要です。

[English README](README.md)

## 主な機能

- **接続チェック：** Blender MCPアドオンによるPython実行と応答を確認し、Blenderのバージョン・シーン名を表示
- **Blenderメッシュ一覧：** 現在のシーン内のメッシュオブジェクト名、頂点数、面数を取得。複数選択可能
- **Blender → Maya：** Blenderで指定したメッシュをFBXで書き出し、Mayaへインポート
- **Maya → Blender：** Mayaで現在選択しているメッシュTransform（またはMesh Shape）のみをFBX経由でBlenderへ送信
- **シンプルなFBXオプション：** 骨／スキン、テクスチャ埋め込み、アニメーションの3項目
- **ワークスペース管理：** FBXと関連ファイルを指定フォルダに保持し、自動削除しない
- **シェルフインストール：** `install.py` をMayaへドラッグ＆ドロップしてシェルフボタンを追加
- **Maya再起動不要のリロード：** `blender_meshport.show(reload=True)` でモジュールを再読み込み
- **Maya標準GUI：** PySide / Shiboken / `QSettings` への直接依存なし

## 動作環境

- Python 3が動作し、**fbxmaya** プラグインが利用できるAutodesk Maya。Maya 2024/2025を想定していますが、環境ごとの確認が必要です。
- **Blender公式MCPアドオン** を導入し、サーバーを起動したBlender。Blender 5.1.1を使用した開発・接続確認の経緯がありますが、すべての転送機能の互換性を保証するものではありません。
- MayaとBlenderが同一PC上で動作し、**同じローカルワークスペースのパス**へアクセスできること。
- Blender MCPアドオンのTCP待ち受け先が `127.0.0.1` にあり、ポートが一致すること（初期値 `9876`、GUIから変更可能）。

**通信方式について：** MeshPortは公式Blender MCPアドオンのローカルTCPインターフェースへ直接接続し、NULL終端JSON形式で通信します。一般的なMCP stdioクライアントではありません。アドオン内部の通信仕様が変更された場合は、Tool側も更新が必要になることがあります。

## インストール方法

1. ZIPを展開し、`__init__.py` と `install.py` を含む `blender_meshport` フォルダをそのまま配置します。
2. Mayaを起動し、ボタンを追加したいシェルフタブを選択します。
3. エクスプローラーから **`blender_meshport/install.py`** をMayaのビューポートにドラッグ＆ドロップします。
4. シェルフに **BMP / MeshPort** ボタンが追加されます。クリックしてToolを起動します。
5. Blender側で公式Blender MCPアドオンのサーバーを起動します。
6. 必要に応じてポートを設定し、転送前に **Workspace Folder** を指定します。

同じシェルフに再インストールすると、同じインストーラー識別子を持つ既存のMeshPortボタンを置き換えます。ボタンは**インストール時の絶対パス**を保持するので、Toolのフォルダを移動した場合は再度ドラッグ＆ドロップしてください。

### Pythonから起動する場合

`blender_meshport` フォルダ自体ではなく、その**親フォルダ**をPythonの検索パスに登録します。

```python
import sys

root = r"C:\Tools\BlenderMeshPort"
if root not in sys.path:
    sys.path.insert(0, root)

import blender_meshport
blender_meshport.show()
```

ソース更新後、Mayaを再起動せずに再読み込みするには、以下を実行します。

```python
import blender_meshport
blender_meshport.show(reload=True)
```

## 使い方

### 1. Blenderとの接続確認

Blender MCPアドオンのサーバーを起動してから、MeshPortの **Check Connection** を押します。接続とコマンド実行が成功すると、例えば次のように表示されます。

```text
Connected: Blender 5.1.1 | Scene
```

メッシュ一覧取得や転送を実行する前にも、自動で接続を確認します。失敗した場合は警告を表示します。

### 2. Blenderのメッシュ一覧を取得

**Refresh Blender Mesh List** を押します。アクティブなBlenderシーンにあるメッシュオブジェクトの名前・頂点数・面数が表示されます。複数行を選択できます。

### 3. BlenderからMayaへインポート

1. **Workspace Folder** を指定します。
2. Blenderのメッシュ一覧を更新し、転送したいメッシュを選択します。
3. 必要に応じてFBXオプションを設定します。
4. **Import to Maya** を押します。

Blenderが共有ワークスペースへFBXを出力し、MayaがそのFBXを `BlenderMeshPort` 名前空間で読み込みます。

### 4. MayaからBlenderへ送信

1. Maya上で送信したい**メッシュTransform、またはMesh Shape** を選択します。対象は現在の選択メッシュに限定されます。親グループを選択するだけでは、配下のメッシュ全体を自動送信する仕様ではありません。
2. **Workspace Folder** とFBXオプションを設定します。
3. **Send to Blender (Selection)** を押します。

Mayaで選択したメッシュ（骨オプション有効時は関連ジョイントも含む）をFBXとして出力し、Blenderにインポートさせます。

### FBXオプション

| オプション | 内容 |
| --- | --- |
| **Include Bones / Skin** | FBXで対応する範囲で、関連する骨やスキニング情報を含めます。 |
| **Embed Textures (FBX)** | FBXにテクスチャを埋め込む設定を使用します。マテリアル・テクスチャの再現性は両DCCの対応状況に依存します。 |
| **Include Animation** | FBXのアニメーション入出力を有効にします。 |

埋め込まれたテクスチャは、インポーターによってFBXと同じ階層に `<FBXファイル名>.fbm` フォルダとして展開される場合があります。生成されるかどうかはインポーター次第で、MeshPort自体が `.fbm` を作成・削除するわけではありません。

## ワークスペースのフォルダ構造

GUIで指定したWorkspace内に、転送方向別のフォルダを作成します。ファイル名には一意の識別子を付け、上書きを防止します。

```text
Workspace/
├── transfers_Maya2Blender/
│   ├── transfer_M2B_<unique-id>.fbx
│   └── transfer_M2B_<unique-id>.fbm/   # インポーターが生成した場合
└── transfers_Blender2Maya/
    ├── transfer_B2M_<unique-id>.fbx
    └── transfer_B2M_<unique-id>.fbm/   # インポーターが生成した場合
```

**転送後のFBXや関連ファイルは自動削除しません。** MayaやBlenderのマテリアルが展開済みテクスチャを参照している可能性があるため、手動削除時も参照関係を確認してください。転送を繰り返すとディスク使用量は増加します。

Workspaceとポート番号はMayaの `cmds.optionVar`（`BlenderMeshPort_workspace_path` / `BlenderMeshPort_port`）に保存します。以前のQt `QSettings` に保存した値は自動移行しないため、必要に応じて再設定してください。

## モジュール構成

```text
blender_meshport/
├── __init__.py           # 起動・モジュールリロード
├── install.py            # Maya D&Dシェルフインストーラー
├── config.py             # 接続初期値・バージョン表示
├── settings.py           # Maya optionVarによる設定保存
├── view.py               # maya.cmds GUI
├── controller.py         # GUIイベント・接続チェック・エラー処理
├── model.py              # TCP通信・転送処理の統括
├── blender_commands.py   # Blenderで実行するPythonコード生成
└── maya_fbx.py           # Maya側のFBX入出力
```

View・Controller・Modelを分離しており、GUIの変更が通信やFBX処理へ波及しにくい設計です。

## トラブルシューティング

| 症状 | 確認ポイント |
| --- | --- |
| `WinError 10061`（接続拒否） | Blender MCPサーバーが**Running**になっているか、Host/Portが一致するかを確認します。 |
| TCP接続は成功するがタイムアウトする | Blenderが操作可能な状態か、MCPアドオンのTCPプロトコルがToolの想定と一致するかを確認します。 |
| メッシュ一覧が空になる | Blenderのアクティブなシーン内にMeshオブジェクトがあるか確認し、一覧を更新します。 |
| FBXを転送できない | Workspaceパス、書き込み権限、共有ファイルへのアクセス、Mayaの `fbxmaya` プラグインを確認します。 |
| テクスチャが表示されない | Embed Texturesの設定、インポート後の参照パス、`.fbm` フォルダを確認します。すべてのマテリアルが完全移行できるとは限りません。 |
| Toolの移動後にシェルフボタンが動かない | `install.py` を再度ドラッグ＆ドロップし、保存された絶対パスを更新します。 |

## 既知の制約・注意点

- **ローカル接続専用：** TCP接続はlocalhostに制限しており、MayaとBlenderが共通ファイルシステムへアクセスできることが前提です。
- **FBX互換性：** マテリアルノード、リグ、スキンウェイト、アニメーション、軸・単位の差は、必要に応じて手動調整してください。
- **UIの応答性：** 通信処理は同期方式のため、長い転送中はMayaのGUIが一時的に応答しなくなる可能性があります。
- **状態の復元：** Maya側のFBX設定を保存・復元し、Blender側はFBX出力後の選択・アクティブオブジェクト・モードを可能な範囲で復元します。状況によってモードが完全に復元できない場合があります。
- **セキュリティ：** Blender側でPythonコードを実行する仕組みを使用します。信頼できるローカルプロセスからのみ利用し、TCP待ち受けポートを外部公開しないでください。
- **動作確認：** 実際のMaya・BlenderでのGUIとFBX双方向転送は、正式リリースに向けて実機確認が必要です。

## ライセンス

現時点ではリポジトリのライセンスを確定していません。プロジェクト管理者が `LICENSE` ファイルを追加するまでは、**オープンソースライセンスや再配布の自由が付与されているものと解釈しないでください。**
