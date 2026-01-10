// AssetFlow API Client Template
import "dart:convert";
import "package:http/http.dart" as http;

class AssetFlowApiClient {
  final String baseUrl;
  
  AssetFlowApiClient({required this.baseUrl});
  
  Future<Map<String, dynamic>> healthCheck() async {
    final response = await http.get(Uri.parse("$baseUrl/api/v1/health/"));
    return json.decode(response.body);
  }
}
