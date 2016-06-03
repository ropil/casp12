function [ partition_image, crosscheck ] = draw_partition( partfile, imagefile )
%SHOW_DOMAIN_PARTITION Visualize a domain partition vector in 2D
%   Expects the domains to be numbered as integers from 1 to the number of
%   domains; no domain numbering gaps.
%
%   partfile - partitioning vector file
%   imagefile - output .png file

    partition = dlmread(partfile);
    partition = partition(:,2);
    num_domains = max(partition);
    increment = 1.0/(num_domains + 1.0);
    crosscheck = partition * partition';
    partition_image = zeros(length(partition));
    for i=1:num_domains
        partition_image = partition_image + i * increment * (crosscheck == i^2);
    end
    f = figure(1);
    imagesc(partition_image);
    saveas(f, imagefile, 'png');
    exit;
end

