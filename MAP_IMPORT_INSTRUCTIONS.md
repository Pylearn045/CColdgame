Unity 导入说明（快速入门）

1) 在仓库根目录生成 JSON 地图：
   python export_map.py --width 96 --height 96
   生成文件 map_96x96.json

2) 在 Unity 中（C#）示例解析：

// 简化的数据容器（与导出结构匹配）
[System.Serializable]
public class MapData {
  public int width;
  public int height;
  public int[][] tiles; // tiles[row][col]
  public int[][] layers; // height layers placeholder
}

// 读取示例（使用 Newtonsoft.Json 或 Unity 的 JsonUtility 需要调整为适配数组类型）
using System.IO;
using UnityEngine;

public class MapImporter : MonoBehaviour {
  public string jsonPath = "map_96x96.json";

  void Start() {
    var path = Path.Combine(Application.dataPath, "..", jsonPath);
    if (!File.Exists(path)) { Debug.LogError("Map JSON not found: " + path); return; }
    var txt = File.ReadAllText(path);
    // 推荐使用 Newtonsoft.Json for jagged arrays
    var map = Newtonsoft.Json.JsonConvert.DeserializeObject<MapData>(txt);
    GenerateGrid(map);
  }

  void GenerateGrid(MapData map) {
    // 示例：创建一个 parent 空 GameObject，按 tiled 单位创建地形块
    var parent = new GameObject("MapRoot");
    for (int r = 0; r < map.height; r++) {
      for (int c = 0; c < map.width; c++) {
        int t = map.tiles[r][c];
        // Instantiate appropriate prefab or Tile based on t
        // Position: (c * tileSize, 0, r * tileSize)
      }
    }
    // 后续：使用 layers 数据生成 3~5 层高度（山地/河谷）
  }
}

3) 后续计划：
- 编写 Unity 编辑器扩展，基于导入的 JSON 快速可视化并编辑图层高度
- 将单位/建筑替换为 3D Prefab，并把寻路改为基于 NavMesh 或格点 A*
