import { ApiClient } from '../locnet/api-generated-client';


export class AuthenticatedApiClient extends ApiClient {
  override PrepareFetchUrl(path: string): URL {
    const webPath = path.replace(/^\/api(?=\/)/, '/web/api');
    return super.PrepareFetchUrl(webPath);
  }
}
