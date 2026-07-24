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
    q = """query($id: String!) { service(id: $id) { id name createdAt } }"""
    return await gql(q, {"id": service_id})

@mcp.tool()
async def railway_service_restart(service_id: str):
    """重启指定服务"""
    q = """mutation($id: String!) { serviceRestart(id: $id) { id } }"""
    return await gql(q, {"id": service_id})

# ─── 部署 ───

@mcp.tool()
async def railway_deployment_list(service_id: str, limit: int = 10):
    """列出服务的最新部署记录"""
    q = """query($id: String!, $first: Int!) {
        service(id: $id) { deployments(first: $first) { edges { node { id status createdAt } } } }
    }"""
    return await gql(q, {"id": service_id, "first": limit})

@mcp.tool()
async def railway_deployment_get(deployment_id: str):
    """获取部署详情"""
    q = """query($id: String!) { deployment(id: $id) { id status createdAt staticUrl } }"""
    return await gql(q, {"id": deployment_id})

@mcp.tool()
async def railway_deployment_logs(deployment_id: str, limit: int = 50):
    """获取部署日志"""
    q = """query($id: String!, $first: Int!) {
        deployment(id: $id) { logs(first: $first) { edges { node { message timestamp } } } }
    }"""
    return await gql(q, {"id": deployment_id, "first": limit})

@mcp.tool()
async def railway_deployment_redeploy(deployment_id: str):
    """重新部署（基于指定部署ID重新触发部署）"""
    q = """mutation($id: String!) { deploymentRedeploy(id: $id) { id status } }"""
    return await gql(q, {"id": deployment_id})

@mcp.tool()
async def railway_deployment_cancel(deployment_id: str):
    """取消正在进行的部署"""
    q = """mutation($id: String!) { deploymentCancel(id: $id) { id status } }"""
    return await gql(q, {"id": deployment_id})

# ─── 环境变量 ───

@mcp.tool()
async def railway_variables_list(service_id: str):
    """列出服务的环境变量"""
    q = """query($id: String!) { service(id: $id) { environment { variables { edges { node { name value } } } } } }"""
    return await gql(q, {"id": service_id})

@mcp.tool()
async def railway_variable_set(service_id: str, name: str, value: str):
    """设置/更新环境变量"""
    q = """mutation($id: String!, $name: String!, $value: String!) {
        serviceVariableUpsert(serviceId: $id, name: $name, value: $value) { name value }
    }"""
    return await gql(q, {"id": service_id, "name": name, "value": value})

@mcp.tool()
async def railway_variable_delete(service_id: str, variable_id: str):
    """删除环境变量"""
    q = """mutation($id: String!) { serviceVariableDelete(id: $id) { id } }"""
    return await gql(q, {"id": variable_id})

# ─── 环境 ───

@mcp.tool()
async def railway_environments_list(project_id: str):
    """列出项目的所有环境（production, preview等）"""
    q = """query($id: String!) { project(id: $id) { environments { edges { node { id name } } } } }"""
    return await gql(q, {"id": project_id})

@mcp.tool()
async def railway_environment_logs(environment_id: str, limit: int = 50):
    """获取环境的日志"""
    q = """query($id: String!, $first: Int!) {
        environment(id: $id) { logs(first: $first) { edges { node { message timestamp } } } }
    }"""
    return await gql(q, {"id": environment_id, "first": limit})

# ─── 域名 ───

@mcp.tool()
async def railway_domains_list(service_id: str):
    """列出服务的域名"""
    q = """query($id: String!) { service(id: $id) { domains { edges { node { id domain status } } } } }"""
    return await gql(q, {"id": service_id})

# ─── 工作区 ───

@mcp.tool()
async def railway_workspaces_list():
    """列出你的工作区"""
    q = """{ me { workspaces { edges { node { id name } } } } }"""
    return await gql(q)

# ─── 主动查岗（特殊） ───

@mcp.tool()
async def railway_project_check(project_id: str):
    """快速查看项目状态：成员、服务数和最新部署"""
    q = """query($id: String!) {
        project(id: $id) {
            id name
            services { edges { node { id name } } }
        }
    }"""
    return await gql(q, {"id": project_id})


if __name__ == "__main__":
    mcp.run(transport="sse")
