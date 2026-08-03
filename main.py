from fastmcp import FastMCP
import httpx
import os

mcp = FastMCP("railway-mcp")

TOKEN = os.environ.get("RAILWAY_API_TOKEN", "")
API_URL = "https://backboard.railway.app/graphql/v2"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

async def gql(query: str, variables: dict = None) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(API_URL, json={"query": query, "variables": variables}, headers=HEADERS)
        data = r.json()
        if "errors" in data:
            raise Exception(f"Railway API error: {data['errors']}")
        return data.get("data", {})

async def _service_project(service_id: str) -> str:
    q = """query($id: String!) { service(id: $id) { projectId } }"""
    data = await gql(q, {"id": service_id})
    return data["service"]["projectId"]

async def _resolve_env(project_id: str) -> str:
    q = """query($id: String!) { project(id: $id) { environments { edges { node { id name } } } } }"""
    data = await gql(q, {"id": project_id})
    envs = data["project"]["environments"]["edges"]
    if not envs:
        raise Exception("project has no environments")
    for e in envs:
        if e["node"]["name"] == "production":
            return e["node"]["id"]
    return envs[0]["node"]["id"]

async def _service_env(service_id: str):
    pid = await _service_project(service_id)
    eid = await _resolve_env(pid)
    return pid, eid

# ─── 项目 ───

@mcp.tool()
async def railway_projects_list():
    """列出你的所有Railway项目"""
    q = """{ projects { edges { node { id name description createdAt } } } }"""
    return await gql(q)

@mcp.tool()
async def railway_project_get(project_id: str):
    """获取指定项目的详细信息"""
    q = """query($id: String!) { project(id: $id) { id name description createdAt } }"""
    return await gql(q, {"id": project_id})

# ─── 服务 ───

@mcp.tool()
async def railway_services_list(project_id: str):
    """列出项目下的所有服务"""
    q = """query($id: String!) { project(id: $id) { services { edges { node { id name } } } } }"""
    return await gql(q, {"id": project_id})

@mcp.tool()
async def railway_service_get(service_id: str):
    """获取服务的详细信息"""
    q = """query($id: String!) { service(id: $id) { id name projectId createdAt } }"""
    return await gql(q, {"id": service_id})

@mcp.tool()
async def railway_service_restart(service_id: str):
    """重启指定服务（对服务做一次重新部署）"""
    pid, eid = await _service_env(service_id)
    q = """mutation($serviceId: String!, $environmentId: String!) {
        serviceInstanceRedeploy(serviceId: $serviceId, environmentId: $environmentId)
    }"""
    return await gql(q, {"serviceId": service_id, "environmentId": eid})

# ─── 部署 ───

@mcp.tool()
async def railway_deployment_list(service_id: str, limit: int = 10):
    """列出服务的最新部署记录"""
    pid, eid = await _service_env(service_id)
    q = """query($serviceId: String!, $environmentId: String!, $first: Int) {
        deployments(input: { serviceId: $serviceId, environmentId: $environmentId }, first: $first) {
            edges { node { id status createdAt } }
        }
    }"""
    return await gql(q, {"serviceId": service_id, "environmentId": eid, "first": limit})

@mcp.tool()
async def railway_deployment_get(deployment_id: str):
    """获取部署详情"""
    q = """query($id: String!) { deployment(id: $id) { id status createdAt staticUrl } }"""
    return await gql(q, {"id": deployment_id})

@mcp.tool()
async def railway_deployment_logs(deployment_id: str, limit: int = 50):
    """获取部署日志"""
    q = """query($id: String!, $first: Int) {
        deploymentLogs(deploymentId: $id, limit: $first) { message timestamp severity }
    }"""
    return await gql(q, {"id": deployment_id, "first": limit})

@mcp.tool()
async def railway_deployment_redeploy(deployment_id: str):
    """重新部署"""
    q = """mutation($id: String!) { deploymentRedeploy(id: $id) { id status } }"""
    return await gql(q, {"id": deployment_id})

@mcp.tool()
async def railway_deployment_cancel(deployment_id: str):
    """取消部署"""
    q = """mutation($id: String!) { deploymentCancel(id: $id) }"""
    return await gql(q, {"id": deployment_id})

# ─── 环境变量 ───

@mcp.tool()
async def railway_variables_list(service_id: str):
    """列出服务的环境变量"""
    pid, eid = await _service_env(service_id)
    q = """query($projectId: String!, $environmentId: String!, $serviceId: String) {
        variables(projectId: $projectId, environmentId: $environmentId, serviceId: $serviceId)
    }"""
    return await gql(q, {"projectId": pid, "environmentId": eid, "serviceId": service_id})

@mcp.tool()
async def railway_variable_set(service_id: str, name: str, value: str):
    """设置/更新单个环境变量"""
    pid, eid = await _service_env(service_id)
    q = """mutation($projectId: String!, $environmentId: String!, $serviceId: String, $name: String!, $value: String!) {
        variableUpsert(input: { projectId: $projectId, environmentId: $environmentId, serviceId: $serviceId, name: $name, value: $value })
    }"""
    return await gql(q, {"projectId": pid, "environmentId": eid, "serviceId": service_id, "name": name, "value": value})

@mcp.tool()
async def railway_variable_delete(service_id: str, name: str):
    """删除服务的一个环境变量（按变量名删除）"""
    pid, eid = await _service_env(service_id)
    q = """mutation($projectId: String!, $environmentId: String!, $serviceId: String, $name: String!) {
        variableDelete(projectId: $projectId, environmentId: $environmentId, serviceId: $serviceId, name: $name)
    }"""
    return await gql(q, {"projectId": pid, "environmentId": eid, "serviceId": service_id, "name": name})

# ─── 环境 ───

@mcp.tool()
async def railway_environments_list(project_id: str):
    """列出项目的所有环境"""
    q = """query($id: String!) { project(id: $id) { environments { edges { node { id name } } } } }"""
    return await gql(q, {"id": project_id})

@mcp.tool()
async def railway_environment_logs(environment_id: str, limit: int = 50):
    """获取环境的日志（跨所有服务）"""
    q = """query($id: String!, $first: Int) {
        environmentLogs(environmentId: $id, limit: $first) { message timestamp severity }
    }"""
    return await gql(q, {"id": environment_id, "first": limit})

# ─── 域名 ───

@mcp.tool()
async def railway_domains_list(service_id: str):
    """列出服务的域名"""
    pid, eid = await _service_env(service_id)
    q = """query($projectId: String!, $environmentId: String!, $serviceId: String!) {
        domains(projectId: $projectId, environmentId: $environmentId, serviceId: $serviceId)
    }"""
    return await gql(q, {"projectId": pid, "environmentId": eid, "serviceId": service_id})

# ─── 工作区 ───

@mcp.tool()
async def railway_workspaces_list():
    """列出你的工作区"""
    q = """{ workspaces { id name } }"""
    return await gql(q)

# ─── 查岗 ───

@mcp.tool()
async def railway_project_check(project_id: str):
    """快速查看项目状态"""
    q = """query($id: String!) {
        project(id: $id) {
            id name
            services { edges { node { id name } } }
        }
    }"""
    return await gql(q, {"id": project_id})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    mcp.run(transport="http", host="0.0.0.0", port=port)
