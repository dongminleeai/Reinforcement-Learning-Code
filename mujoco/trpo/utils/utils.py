import math
import torch

def get_action(mu, std):
    action = torch.normal(mu, std)
    action = action.data.numpy()
    return action

# logarithm의 property을 이용하여 ratio를 만들 때 사용하기 위한
# normal distribution의 probability density
def log_prob_density(x, mu, std):
    log_density = -(x - mu).pow(2) / (2 * std.pow(2)) \
                     - 0.5 * math.log(2 * math.pi)
    return log_density.sum(1, keepdim=True)


def hessian_vector_product(actor, states, p):
    p.detach()
    kl = kl_divergence(old_actor=actor, new_actor=actor, states=states)
    kl = kl.mean()
    kl_grad = torch.autograd.grad(kl, actor.parameters(), create_graph=True)
    kl_grad = flat_grad(kl_grad)  # check kl_grad == 0

    kl_grad_p = (kl_grad * p).sum()
    kl_hessian_p = torch.autograd.grad(kl_grad_p, actor.parameters())
    kl_hessian_p = flat_hessian(kl_hessian_p)

    return kl_hessian_p + 0.1 * p

def kl_divergence(old_actor, new_actor, states):
    mu, std = new_actor(torch.Tensor(states))
    mu_old, std_old = old_actor(torch.Tensor(states))
    mu_old = mu_old.detach()
    std_old = std_old.detach()

    # kl divergence between old policy and new policy : D( pi_old || pi_new )
    # pi_old -> mu_old, std_old / pi_new -> mu, std
    # be careful of calculating KL-divergence. It is not symmetric metric
    kl = (std_old.pow(2) + (mu_old - mu).pow(2)) / (2.0 * std.pow(2)) - 0.5
    return kl.sum(1, keepdim=True)


def flat_grad(grads):
    grad_flatten = []
    for grad in grads:
        grad_flatten.append(grad.view(-1))
    grad_flatten = torch.cat(grad_flatten)
    return grad_flatten

def flat_hessian(hessians):
    hessians_flatten = []
    for hessian in hessians:
        hessians_flatten.append(hessian.contiguous().view(-1))
    hessians_flatten = torch.cat(hessians_flatten).data
    return hessians_flatten


def flat_params(model):
    params = []
    for param in model.parameters():
        params.append(param.data.view(-1))
    params_flatten = torch.cat(params)
    return params_flatten

def update_model(model, new_params):
    index = 0
    for params in model.parameters():
        params_length = len(params.view(-1))
        new_param = new_params[index: index + params_length]
        new_param = new_param.view(params.size())
        params.data.copy_(new_param)
        index += params_length




