function [ partition_image, crosscheck ] = show_domain_partition( partition )
%SHOW_DOMAIN_PARTITION Visualize a domain partition vector in 2D
%   Expects the domains to be numbered as integers from 1 to the number of
%   domains; no domain numbering gaps.
%
%   partition - partitioning vector

    num_domains = max(partition);
    increment = 1.0/(num_domains + 1.0);
    crosscheck = partition * partition';
    partition_image = zeros(length(partition));
    for i=1:num_domains
        partition_image = partition_image + i * increment * (crosscheck == i^2);
    end
    imagesc(partition_image)
end

